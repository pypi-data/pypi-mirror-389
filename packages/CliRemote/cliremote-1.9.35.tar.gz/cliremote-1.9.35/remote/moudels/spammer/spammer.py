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
    """
    Robust debug-friendly wrapper around build_final_text.
    - Attempts build_final_text(spam_config) then build_final_text()
    - Introspects presence of helper functions used by build_final_text
      (get_random_text, _caption_from_config, build_mentions, _extract_from_message)
    - Logs return values and exceptions at each step.
    """
    try:
        logger.debug(f"{acc_phone}: _perform_action_use_final_text START - spam_config keys: {list(spam_config.keys())}")

        # Introspect helper functions if available in the same module as build_final_text
        modul = getattr(build_final_text, "__module__", None)
        helper_info = {}
        try:
            # try to import the module object where build_final_text is defined
            import importlib
            mod = importlib.import_module(modul) if modul else None
        except Exception:
            mod = None

        def _safe_call(func_name, *args, **kwargs):
            """Try calling helper from module (if exists), return tuple(success, value_or_exc)"""
            if not mod:
                return False, f"module_not_imported_for_{func_name}"
            fn = getattr(mod, func_name, None)
            if not fn:
                return False, f"{func_name}_not_found"
            try:
                v = fn(*args, **kwargs)
                # if coroutine, await it
                if asyncio.iscoroutine(v):
                    # We'll run it synchronously here because helpers likely sync
                    # but to be safe, await it properly
                    return True, asyncio.get_event_loop().run_until_complete(v)
                return True, v
            except Exception as e:
                return False, e

        # Log availability of common helpers
        helpers = ["get_random_text", "_caption_from_config", "build_mentions", "_extract_from_message"]
        for h in helpers:
            ok, val = _safe_call(h) if mod else (False, "module_missing")
            helper_info[h] = {"present": ok, "result": repr(val) if not isinstance(val, Exception) else f"EXC:{type(val).__name__}:{val}"}
        logger.debug(f"{acc_phone}: helper introspect: {helper_info}")

        # 1) Try calling build_final_text(spam_config)
        text = None
        try:
            try:
                text = build_final_text(spam_config)
                # If returns coroutine (unlikely), await it
                if asyncio.iscoroutine(text):
                    text = await text
                logger.debug(f"{acc_phone}: build_final_text(spam_config) returned (len={len(text) if text is not None else 'None'}).")
            except TypeError as te:
                logger.debug(f"{acc_phone}: build_final_text(spam_config) TypeError: {te}; will try build_final_text() fallback.")
                text = None
            except Exception as e:
                logger.warning(f"{acc_phone}: build_final_text(spam_config) raised {type(e).__name__}: {e}")
                text = None
        except Exception as e:
            logger.exception(f"{acc_phone}: Unexpected while calling build_final_text(spam_config): {e}")
            text = None

        # 2) Fallback to build_final_text() if needed
        if not text:
            try:
                text = build_final_text()
                if asyncio.iscoroutine(text):
                    text = await text
                logger.debug(f"{acc_phone}: build_final_text() returned (len={len(text) if text is not None else 'None'}).")
            except Exception as e:
                logger.warning(f"{acc_phone}: build_final_text() raised {type(e).__name__}: {e}")
                text = None

        # 3) If still empty, try constructing text from helpers directly (best-effort)
        if not text:
            fallback_parts = []
            # try get_random_text
            if mod and hasattr(mod, "get_random_text"):
                try:
                    gr = getattr(mod, "get_random_text")()
                    if asyncio.iscoroutine(gr):
                        gr = await gr
                    fallback_parts.append(str(gr or ""))
                    logger.debug(f"{acc_phone}: get_random_text() -> {repr(gr)}")
                except Exception as e:
                    logger.warning(f"{acc_phone}: get_random_text() raised {type(e).__name__}: {e}")
            # try caption
            if mod and hasattr(mod, "_caption_from_config"):
                try:
                    cap = getattr(mod, "_caption_from_config")()
                    if asyncio.iscoroutine(cap):
                        cap = await cap
                    fallback_parts.append(str(cap or ""))
                    logger.debug(f"{acc_phone}: _caption_from_config() -> {repr(cap)}")
                except Exception as e:
                    logger.warning(f"{acc_phone}: _caption_from_config() raised {type(e).__name__}: {e}")
            # try mentions
            if mod and hasattr(mod, "build_mentions"):
                try:
                    mn = getattr(mod, "build_mentions")()
                    if asyncio.iscoroutine(mn):
                        mn = await mn
                    fallback_parts.append(str(mn or ""))
                    logger.debug(f"{acc_phone}: build_mentions() -> {repr(mn)}")
                except Exception as e:
                    logger.warning(f"{acc_phone}: build_mentions() raised {type(e).__name__}: {e}")

            constructed = "".join([p for p in fallback_parts if p])
            if constructed:
                text = constructed
                logger.debug(f"{acc_phone}: constructed fallback text from helpers (len={len(text)}).")
            else:
                logger.debug(f"{acc_phone}: No fallback parts available to construct text.")

        # 4) Final safety: ensure non-empty
        if not text or not str(text).strip():
            logger.info(f"{acc_phone}: final text is empty after all attempts; returning explicit marker.")
            text = "[EMPTY TEXT FROM finaly_text]"

        # yield to loop
        await asyncio.sleep(0)

        # log full text length and a safe preview (avoid huge dumps)
        preview = str(text)[:1000]
        logger.info(f"[SIM-SEND] {acc_phone} -> {spam_config.get('spamTarget','<no-target>')} | text_len={len(str(text))} preview={preview!r}")

        # success
        return True

    except Exception as e:
        logger.exception(f"{acc_phone}: exception in perform_action (final): {e}")
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
