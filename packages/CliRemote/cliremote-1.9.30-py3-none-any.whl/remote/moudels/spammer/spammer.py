# remote/moudels/spammer/spammer.py
"""
Safe, asyncio-based spammer module (SIMULATED).
- Uses build_final_text() from your project (finaly_text).
- Prints the action instead of sending any network message.
- Uses asyncio.create_task (no threads), batching and semaphore-based concurrency.
- Compatible with core_handler which expects SpammerThreadingRunner with start()/stop().
"""

import asyncio
import logging
import os
import random
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# try to import your finaly_text builder
try:
    from ..text.finaly_text import build_final_text
except Exception:
    # fallback simple builder if import fails
    def build_final_text(*args, **kwargs):
        return f"[fallback demo message] {datetime.utcnow().isoformat()}"

# logging setup with high-resolution timestamps
class NanoFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        ns = int((record.created - int(record.created)) * 1_000_000_000)
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}.{ns:09d}"

logger = logging.getLogger("remote.moudels.spammer")
logger.setLevel(logging.INFO)
os.makedirs("logs", exist_ok=True)
fh = logging.FileHandler("logs/spammer_realmode_safe.log", encoding="utf-8")
fh.setFormatter(NanoFormatter("%(asctime)s - %(levelname)s - %(message)s"))
if not any(
    isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "").endswith("spammer_realmode_safe.log")
    for h in logger.handlers
):
    logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setFormatter(NanoFormatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(ch)

# try to import project's account/client managers if present
try:
    from ..account import account_manager
except Exception:
    account_manager = None

try:
    from ..account.client import client_manager
except Exception:
    client_manager = None

# singleton placeholder to mimic previous API
_spammer_runner_singleton: Optional["SpammerThreadingRunner"] = None

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

# core simulated action using build_final_text
async def _perform_action_use_final_text(acc_phone: str, spam_config: Dict[str, Any]) -> bool:
    try:
        # try calling build_final_text in a couple of common signatures
        try:
            text = build_final_text()
        except TypeError:
            try:
                text = build_final_text(spam_config)
            except Exception:
                text = f"[generated] {datetime.utcnow().isoformat()}"

        # short yield to event loop
        await asyncio.sleep(0)

        # optional transient failure simulation
        fail_rate = float(spam_config.get("demo_fail_rate", 0.0))
        if fail_rate > 0.0 and random.random() < fail_rate:
            logger.warning(f"{acc_phone}: simulated transient failure (demo).")
            return False

        # SIMULATED ACTION: print the "send" using the generated text
        target = spam_config.get("spamTarget", "<no-target>")
        print(f"[SIM-SEND] {acc_phone} -> {target} | text: {text[:400]!r}")
        logger.info(f"{acc_phone}: simulated send printed.")
        return True

    except Exception as e:
        logger.exception(f"{acc_phone}: exception in perform_action: {e}")
        return False

# safe wrapper with per-account lock
async def safe_action(acc_phone: str, spam_config: Dict[str, Any], remove_client_from_pool: Callable[[str], None]) -> bool:
    if not hasattr(safe_action, "_locks"):
        safe_action._locks = {}
    locks = safe_action._locks
    if acc_phone not in locks:
        locks[acc_phone] = asyncio.Lock()

    async with locks[acc_phone]:
        ok = await _perform_action_use_final_text(acc_phone, spam_config)
        # optionally remove client on persistent failure:
        # if not ok: remove_client_from_pool(acc_phone)
        return ok

# main async runner
async def run_spammer(spam_config: Dict[str, Any], remove_client_from_pool: Callable[[str], None]):
    base_delay = float(spam_config.get("TimeSleep", 2.0))
    batch_size = max(1, int(spam_config.get("BATCH_SIZE", 2)))
    concurrency = max(1, int(spam_config.get("CONCURRENCY", 4)))
    total_ok = 0

    logger.info(f"Spammer (safe-sim) starting: delay={base_delay}s batch={batch_size} concurrency={concurrency}")
    sem = asyncio.Semaphore(concurrency)

    try:
        while spam_config.get("run", False):
            accounts = await _get_accounts_from_manager(spam_config)
            if not accounts:
                logger.warning("No accounts found; sleeping briefly.")
                await asyncio.sleep(1.0)
                continue

            for i in range(0, len(accounts), batch_size):
                if not spam_config.get("run", False):
                    break
                batch = accounts[i : i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1} size={len(batch)}")

                async def _task_for(acc: str):
                    async with sem:
                        return await safe_action(acc, spam_config, remove_client_from_pool)

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
        logger.info(f"Spammer safe-sim stopped. total_ok={total_ok}")

# compatibility wrapper expected by core_handler (start/stop API)
class SpammerThreadingRunner:
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
            raise RuntimeError("SpammerThreadingRunner.start() must be called from an asyncio context (pyrogram handler).")
        self._loop = loop
        self.spam_config["run"] = True
        self._task = loop.create_task(run_spammer(self.spam_config, self.remove_client_from_pool))
        logger.info("SpammerThreadingRunner started (async task created).")

    def stop(self):
        logger.info("Stop requested for SpammerThreadingRunner")
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

# singleton helpers
def start_spammer_thread(spam_config: Dict[str, Any], remove_client_from_pool: Callable[[str], None]):
    global _spammer_runner_singleton
    if _spammer_runner_singleton and _spammer_runner_singleton._task and not _spammer_runner_singleton._task.done():
        logger.info("Spammer already running (singleton).")
        return _spammer_runner_singleton
    runner = SpammerThreadingRunner(spam_config, remove_client_from_pool)
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
