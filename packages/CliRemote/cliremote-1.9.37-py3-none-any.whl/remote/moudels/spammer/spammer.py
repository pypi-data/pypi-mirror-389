# remote/moudels/spammer/spammer.py
"""
Real sending spammer module (asyncio-based).
- Uses build_final_text() from your project (finaly_text).
- Uses client_manager.get_or_start_client(...) to obtain Pyrogram clients.
- Controls concurrency with Semaphore and per-account locks.
- Handles FloodWait, ChatWriteForbidden, Auth errors, timeouts and backoff.
- Requires environment variable ENABLE_REAL_SEND=1 to actually send messages
  (otherwise it will run in simulated mode, printing/logging instead).
"""

import asyncio
import logging
import os
import random
import re
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from pyrogram import errors

# try to import your finaly_text builder
try:
    from ..text.finaly_text import build_final_text
except Exception:
    def build_final_text(*args, **kwargs):
        return f"[fallback demo message] {datetime.utcnow().isoformat()}"

# try to import project's account/client managers if present
try:
    from ..account import account_manager
except Exception:
    account_manager = None

try:
    from ..account.client import client_manager
except Exception:
    client_manager = None

# Logging setup
class NanoFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        ns = int((record.created - int(record.created)) * 1_000_000_000)
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}.{ns:09d}"

logger = logging.getLogger("remote.moudels.spammer_real")
logger.setLevel(logging.INFO)
os.makedirs("logs", exist_ok=True)
fh = logging.FileHandler("logs/spammer_real.log", encoding="utf-8")
fh.setFormatter(NanoFormatter("%(asctime)s - %(levelname)s - %(message)s"))
if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "").endswith("spammer_real.log") for h in logger.handlers):
    logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setFormatter(NanoFormatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(ch)

# singleton placeholder
_spammer_runner_singleton: Optional["SpammerAsyncRunner"] = None

# normalize target (kept for compatibility with core_handler)
def _normalize_target_for_spam(raw: str):
    if raw is None:
        return None, None, None
    s = str(raw).strip()
    original_has_joinchat = "joinchat" in s.lower()
    s = re.sub(r"^(?:https?://)", "", s, flags=re.I)
    s = re.sub(r"^www\.", "", s, flags=re.I)
    if "/" in s:
        s = s.split("/")[-1]
    s = s.split("?")[0].strip().strip("<>\"'")
    if s.startswith("@"):
        s = s[1:].strip()
    if s.startswith("+"):
        return "invite", s.lstrip("+").strip(), False
    if s.lstrip("-").isdigit():
        try:
            return "chat_id", int(s), None
        except Exception:
            pass
    if re.match(r"^[A-Za-z0-9_\-]{8,}$", s):
        if len(s) >= 20:
            return "invite", s, original_has_joinchat
        return "username", s, None
    return "username", s, None

# helper: obtain accounts list (from account_manager or spam_config fallback)
async def _get_accounts_from_manager(spam_config: Dict[str, Any]) -> List[str]:
    if account_manager is not None:
        try:
            accs = account_manager.accounts()
            if asyncio.iscoroutine(accs):
                accs = await accs
            return list(accs)
        except Exception:
            logger.exception("Failed to get accounts from account_manager; falling back to spam_config['accounts']")
    return list(spam_config.get("accounts", []))

# internal per-account rate tracker
_account_last_sent: Dict[str, float] = {}  # phone -> timestamp (epoch)
# optional per-account tokens (simple token-bucket-ish)
_account_tokens: Dict[str, float] = {}  # phone -> tokens
_account_token_ts: Dict[str, float] = {}  # phone -> last refill time

def _ensure_account_token_state(phone: str, rate_per_minute: float):
    """Initialize token state for account if missing. rate_per_minute: allowed messages per minute."""
    if phone not in _account_tokens:
        _account_tokens[phone] = 1.0  # start with one token
        _account_token_ts[phone] = time.time()
    # token refill rate per second:
    refill_per_sec = rate_per_minute / 60.0
    now = time.time()
    elapsed = now - _account_token_ts[phone]
    _account_tokens[phone] = min( max(_account_tokens[phone], 0.0) + elapsed * refill_per_sec, max(1.0, rate_per_minute) )
    _account_token_ts[phone] = now

async def _acquire_token(phone: str, rate_per_minute: float, timeout: float = 30.0) -> bool:
    """Wait until the account has at least 1 token or timeout (returns True if token acquired)."""
    start = time.time()
    while True:
        _ensure_account_token_state(phone, rate_per_minute)
        if _account_tokens.get(phone, 0.0) >= 1.0:
            _account_tokens[phone] -= 1.0
            return True
        if time.time() - start > timeout:
            return False
        await asyncio.sleep(0.5)

# safe send: real send via client_manager
async def safe_send_real(acc_phone: str, spam_config: Dict[str, Any], text: str, remove_client_from_pool: Callable[[str], None]) -> bool:
    """
    Attempts to send a real message using client's send_message.
    Handles reconnect, FloodWait, temporary RPC errors, rate-limiting, and common auth errors.
    Returns True if message successfully sent, False otherwise.
    """
    # guard for enabling real sends
    enable_real = os.environ.get("ENABLE_REAL_SEND", "0") == "1"
    if not enable_real:
        # fallback to simulated behavior (log and return True)
        logger.info(f"{acc_phone}: REAL SEND DISABLED (ENABLE_REAL_SEND!=1). Simulating send.")
        logger.info(f"[SIM-SEND] {acc_phone} -> {spam_config.get('spamTarget','<no-target>')} | text_len={len(text)}")
        return True

    # per-account rate limiting (messages per minute)
    rate_per_minute = float(spam_config.get("RATE_PER_MINUTE_PER_ACCOUNT", 1.0))
    token_acquired = await _acquire_token(acc_phone, rate_per_minute, timeout=30.0)
    if not token_acquired:
        logger.warning(f"{acc_phone}: rate token acquisition timed out; skipping send.")
        return False

    # get or start client
    try:
        cli = await client_manager.get_or_start_client(acc_phone)
        if not cli:
            logger.warning(f"{acc_phone}: client unavailable from client_manager.")
            return False
    except Exception as e:
        logger.exception(f"{acc_phone}: error while get_or_start_client: {e}")
        remove_client_from_pool(acc_phone)
        return False

    # ensure per-client lock exists (prefer using client_manager.client_locks if available)
    locks = None
    try:
        locks = getattr(client_manager, "client_locks", None)
    except Exception:
        locks = None
    if locks is None:
        # fallback local locks mapping
        if not hasattr(safe_send_real, "_local_locks"):
            safe_send_real._local_locks = {}
        locks = safe_send_real._local_locks

    if acc_phone not in locks:
        locks[acc_phone] = asyncio.Lock()

    async with locks[acc_phone]:
        try:
            if not getattr(cli, "is_connected", False):
                try:
                    await cli.start()
                    logger.info(f"{acc_phone}: reconnected client before send.")
                except Exception as e:
                    logger.error(f"{acc_phone}: failed to start client before send: {e}")
                    remove_client_from_pool(acc_phone)
                    return False

            target = spam_config.get("spamTarget")
            if target is None:
                logger.warning(f"{acc_phone}: no spamTarget specified.")
                return False

            # send with retries & floodwait/backoff handling
            max_attempts = int(spam_config.get("SEND_RETRY_ATTEMPTS", 3))
            attempt = 0
            backoff_initial = float(spam_config.get("SEND_BACKOFF_INITIAL", 1.0))
            while attempt < max_attempts:
                attempt += 1
                try:
                    # actual send (real)
                    await cli.send_message(target, text)
                    logger.info(f"{acc_phone}: ✅ Message sent (attempt {attempt}).")
                    _account_last_sent[acc_phone] = time.time()
                    return True

                except errors.FloodWait as fw:
                    wait_for = int(getattr(fw, "value", getattr(fw, "x", 5)))
                    # clamp wait to a reasonable max (in case fw.value is huge)
                    max_wait = int(spam_config.get("FLOODWAIT_MAX", 300))
                    wait_for = min(wait_for, max_wait)
                    logger.warning(f"{acc_phone}: FloodWait {wait_for}s (attempt {attempt}). Sleeping and retrying.")
                    await asyncio.sleep(wait_for + 0.5)

                except (errors.RPCError, errors.BadRequest, asyncio.TimeoutError) as e:
                    # transient errors: jittered exponential backoff
                    delay = backoff_initial * (2 ** (attempt - 1)) + random.random()
                    max_delay = float(spam_config.get("SEND_RETRY_MAX_BACKOFF", 60.0))
                    delay = min(delay, max_delay)
                    logger.warning(f"{acc_phone}: transient send error {type(e).__name__}: {e} — backoff {delay:.1f}s (attempt {attempt}).")
                    await asyncio.sleep(delay)

                except errors.AuthKeyUnregistered:
                    logger.error(f"{acc_phone}: AuthKeyUnregistered — session invalid. Removing from pool.")
                    remove_client_from_pool(acc_phone)
                    return False

                except errors.UserDeactivated:
                    logger.error(f"{acc_phone}: UserDeactivated — account disabled. Removing from pool.")
                    remove_client_from_pool(acc_phone)
                    return False

                except errors.ChatWriteForbidden:
                    logger.warning(f"{acc_phone}: ChatWriteForbidden — cannot send to {target}.")
                    return False

                except Exception as e:
                    # unknown error: try limited backoff else remove
                    logger.exception(f"{acc_phone}: Unexpected exception during send (attempt {attempt}): {e}")
                    await asyncio.sleep(min(5 * attempt, 30))

            # if attempts exhausted
            logger.error(f"{acc_phone}: All {max_attempts} send attempts failed.")
            return False

        except Exception as e:
            logger.exception(f"{acc_phone}: fatal error in safe_send_real: {e}")
            try:
                remove_client_from_pool(acc_phone)
            except Exception:
                pass
            return False

# wrapper that chooses between simulation and real
async def safe_send(acc_phone: str, spam_config: Dict[str, Any], text: str, remove_client_from_pool: Callable[[str], None]) -> bool:
    return await safe_send_real(acc_phone, spam_config, text, remove_client_from_pool)

# main async runner
async def run_spammer(spam_config: Dict[str, Any], remove_client_from_pool: Callable[[str], None]):
    base_delay = float(spam_config.get("TimeSleep", 2.0))
    batch_size = max(1, int(spam_config.get("BATCH_SIZE", 2)))
    concurrency = max(1, int(spam_config.get("CONCURRENCY", 4)))
    total_ok = 0

    logger.info(f"Spammer (real) starting: delay={base_delay}s batch={batch_size} concurrency={concurrency}")

    sem = asyncio.Semaphore(concurrency)

    try:
        while spam_config.get("run", False):
            accounts = await _get_accounts_from_manager(spam_config)
            if not accounts:
                logger.warning("No accounts found; sleeping briefly.")
                await asyncio.sleep(1.0)
                continue

            # build message text using build_final_text (try passing spam_config first)
            text = None
            try:
                try:
                    text = build_final_text(spam_config)
                except TypeError:
                    text = build_final_text()
            except Exception as e:
                logger.exception(f"Failed to build final text: {e}")
                text = None

            if not text or not str(text).strip():
                logger.warning("Final text empty; skipping this round.")
                await asyncio.sleep(max(1.0, base_delay))
                continue

            # process in batches
            for i in range(0, len(accounts), batch_size):
                if not spam_config.get("run", False):
                    break
                batch = accounts[i : i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1} size={len(batch)}")

                async def _task_for(acc: str):
                    async with sem:
                        try:
                            return await safe_send(acc, spam_config, text, remove_client_from_pool)
                        except Exception as e:
                            logger.exception(f"{acc}: exception in _task_for: {e}")
                            return False

                results = await asyncio.gather(*[_task_for(acc) for acc in batch], return_exceptions=False)
                succ = sum(1 for r in results if r is True)
                total_ok += succ
                logger.info(f"Batch done: success={succ}/{len(batch)} total_ok={total_ok}")
                await asyncio.sleep(base_delay)

    except asyncio.CancelledError:
        logger.info("run_spammer cancelled")
        raise
    except Exception as e:
        logger.exception(f"Unhandled error in run_spammer: {e}")
    finally:
        logger.info(f"Spammer stopped. total_ok={total_ok}")
        # try to stop all clients politely
        try:
            if client_manager:
                await client_manager.stop_all_clients()
        except Exception:
            logger.exception("Error stopping clients in finally block")

# compatibility wrapper expected by core_handler (start/stop API)
class SpammerAsyncRunner:
    """
    Compatibility wrapper. Exposes start() and stop() (sync) methods but runs async task internally.
    Must be started from within an active asyncio event loop (pyrogram handler context).
    """
    def __init__(self, spam_config: Dict[str, Any], remove_client_from_pool: Callable[[str], None]):
        self.spam_config = spam_config or {}
        self.remove_client_from_pool = remove_client_from_pool
        self._task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self):
        if self._task and not self._task.done():
            logger.info("Spammer already running")
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("SpammerAsyncRunner.start() must be called from an asyncio context (pyrogram handler).")
        self._loop = loop
        self.spam_config["run"] = True
        self._task = loop.create_task(run_spammer(self.spam_config, self.remove_client_from_pool))
        logger.info("SpammerAsyncRunner started (async task created).")

    def stop(self):
        logger.info("Stop requested for SpammerAsyncRunner")
        try:
            self.spam_config["run"] = False
        except Exception:
            pass
        if self._task and not self._task.done():
            if self._loop and self._loop.is_running():
                def _cancel():
                    if self._task and not self._task.done():
                        self._task.cancel()
                try:
                    self._loop.call_soon_threadsafe(_cancel)
                except Exception:
                    self._task.cancel()
            else:
                self._task.cancel()

# singleton helpers (former API)
def start_spammer_thread(spam_config: Dict[str, Any], remove_client_from_pool: Callable[[str], None]):
    global _spammer_runner_singleton
    if _spammer_runner_singleton and _spammer_runner_singleton._task and not _spammer_runner_singleton._task.done():
        logger.info("Spammer already running (singleton).")
        return _spammer_runner_singleton
    runner = SpammerAsyncRunner(spam_config, remove_client_from_pool)
    runner.start()
    _spammer_runner_singleton = runner
    return runner

def stop_spammer_thread():
    global _spammer_runner_singleton
    if _spammer_runner_singleton:
        _spammer_runner_singleton.stop()
        _spammer_runner_singleton = None
        logger.info("Spammer stopped (singleton cleared).")
    else:
        logger.info("No running spammer to stop.")
