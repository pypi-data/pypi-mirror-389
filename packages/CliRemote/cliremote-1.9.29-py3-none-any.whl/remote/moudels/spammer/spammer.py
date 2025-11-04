# remote/moudels/spammer/spammer.py
import asyncio
import logging
import os
import random
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# ================== logging setup ==================
class NanoFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        ns = int((record.created - int(record.created)) * 1_000_000_000)
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}.{ns:09d}"

logger = logging.getLogger("remote.moudels.spammer.spammer")
logger.setLevel(logging.INFO)
os.makedirs("logs", exist_ok=True)
fh = logging.FileHandler("logs/spammer_profile_change.log", encoding="utf-8")
fh.setFormatter(NanoFormatter("%(asctime)s - %(levelname)s - %(message)s"))
if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "").endswith("spammer_profile_change.log") for h in logger.handlers):
    logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setFormatter(NanoFormatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(ch)

# ================== try import account client manager ==================
# this module expects a client manager with an async get_or_start_client(phone) -> Client
# and remove_client_from_pool(phone) callable (as in your repo).
try:
    from ..account import account_manager
except Exception:
    account_manager = None

try:
    from ..account.client import client_manager
except Exception:
    client_manager = None

# ================== normalize target (keeps compatibility) ==================
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

# ================== helper: perform profile first-name change ==================
async def _attempt_change_first_name(acc_phone: str, new_first_name: str):
    """
    دریافت client مربوط به acc_phone و تغییر first_name به new_first_name.
    از client_manager.get_or_start_client استفاده می‌شود (اگر موجود باشد).
    """
    # get client (project-specific API)
    if client_manager is None:
        raise RuntimeError("client_manager not available in environment.")

    cli = None
    # try to get or start client using common function names
    # your project may provide client_manager.get_or_start_client or client_manager.get_any_client etc.
    if hasattr(client_manager, "get_or_start_client"):
        maybe = client_manager.get_or_start_client(acc_phone)
        if asyncio.iscoroutine(maybe):
            cli = await maybe
        else:
            cli = maybe
    elif hasattr(client_manager, "get_client"):
        maybe = client_manager.get_client(acc_phone)
        if asyncio.iscoroutine(maybe):
            cli = await maybe
        else:
            cli = maybe
    else:
        # fallback to any other available helper
        raise RuntimeError("client_manager has no known get_or_start_client/get_client API.")

    if not cli:
        raise RuntimeError(f"No client for {acc_phone}")

    # now try to update profile first name
    # Pyrogram: await cli.update_profile(first_name="...") or await cli.set_profile(first_name=...)
    # Use update_profile which exists on pyrogram.Client
    # We keep this in try/except to remove client from pool on fatal errors
    try:
        # Ensure client is started (connected)
        if not getattr(cli, "is_connected", False):
            # try start (client.start is coroutine)
            if hasattr(cli, "start"):
                maybe = cli.start()
                if asyncio.iscoroutine(maybe):
                    await maybe

        # perform the change
        # Note: Pyrogram API uses update_profile(...) to change first_name / last_name.
        if hasattr(cli, "update_profile"):
            coro = cli.update_profile(first_name=new_first_name)
            if asyncio.iscoroutine(coro):
                await coro
            else:
                # some client APIs might be sync wrappers — assume it's fine
                pass
        else:
            # fallback: try set_profile or edit_profile variants
            if hasattr(cli, "set_profile"):
                maybe = cli.set_profile(first_name=new_first_name)
                if asyncio.iscoroutine(maybe):
                    await maybe
            else:
                raise RuntimeError("Client has no update_profile/set_profile method.")
        return True

    finally:
        # no forced stop here — keep session alive for future ops
        pass

# ================== safe_change_name: wraps locks and errors ==================
async def safe_change_first_name(acc_phone: str, spam_config: Dict[str, Any], new_first_name: str, remove_client_from_pool: Callable[[str], None]) -> bool:
    """
    امن‌تر اجرا کردن تغییر first_name:
    - از lock per-account استفاده می‌کند تا هم‌زمانی روی یک سشن مشکل‌ساز نشود
    - در شرایطی مانند auth error یا user deactivated، سعی می‌کند client را از pool حذف کند
    """
    try:
        # ensure locks container
        if not hasattr(safe_change_first_name, "_locks"):
            safe_change_first_name._locks = {}
        locks = safe_change_first_name._locks
        if acc_phone not in locks:
            locks[acc_phone] = asyncio.Lock()

        async with locks[acc_phone]:
            # simulate transient failures optionally (demo_fail_rate default 0.0)
            fail_rate = float(spam_config.get("demo_fail_rate", 0.0))
            if fail_rate > 0.0 and random.random() < fail_rate:
                logger.warning(f"{acc_phone}: ⚠️ simulated transient error (demo).")
                return False

            try:
                ok = await _attempt_change_first_name(acc_phone, new_first_name)
                if ok:
                    logger.info(f"{acc_phone}: ✅ First name changed to {new_first_name}.")
                return bool(ok)
            except Exception as e:
                # On some fatal errors, drop client from pool if possible
                logger.warning(f"{acc_phone}: ❌ Error changing name - {type(e).__name__}: {e}")
                try:
                    if client_manager is not None and hasattr(client_manager, "remove_client_from_pool"):
                        client_manager.remove_client_from_pool(acc_phone)
                except Exception:
                    logger.debug("remove_client_from_pool failed", exc_info=True)
                return False

    except Exception as e:
        logger.exception(f"{acc_phone}: 💥 Fatal error in safe_change_first_name: {e}")
        try:
            if client_manager is not None and hasattr(client_manager, "remove_client_from_pool"):
                client_manager.remove_client_from_pool(acc_phone)
        except Exception:
            pass
        return False

# ================== main async runner ==================
async def run_spammer(spam_config: Dict[str, Any], remove_client_from_pool: Callable[[str], None]):
    """
    حلقهٔ اصلی:
    - لیست اکانت‌ها را از account_manager.accounts() می‌گیرد در صورت موجود بودن
    - برای هر حساب، تابع safe_change_first_name را اجرا می‌کند (با batching و semaphore)
    - توجه: spam_config باید شامل:
        - "run": bool
        - optionally: "accounts": list[str] fallback
        - "TimeSleep", "BATCH_SIZE", "CONCURRENCY"
        - "new_first_name": str (default "FIRSTNAMETEST")
    """
    base_delay = float(spam_config.get("TimeSleep", 2.0))
    batch_size = 1
    concurrency = 1
    new_first_name = "FIRSTNAMETEST"
    total_changed = 0

    logger.info(f"🚀 Spammer (profile-change) started | Delay: {base_delay:.3f}s | Batch size: {batch_size} | Concurrency: {concurrency}")

    sem = asyncio.Semaphore(concurrency)

    async def _get_accounts() -> List[str]:
        if account_manager is not None:
            try:
                accounts = account_manager.accounts()
                if asyncio.iscoroutine(accounts):
                    accounts = await accounts
                return list(accounts)
            except Exception:
                logger.exception("Failed to get accounts from account_manager; falling back to spam_config['accounts']")
        return list(spam_config.get("accounts", []))

    try:
        while spam_config.get("run", False):
            accounts = await _get_accounts()
            if not accounts:
                logger.warning("❌ هیچ اکانتی فعال نیست — در صورت نیاز spam_config['accounts'] را تنظیم کن.")
                await asyncio.sleep(1.0)
                continue

            # split into batches
            for i in range(0, len(accounts), batch_size):
                if not spam_config.get("run", False):
                    break
                batch = accounts[i:i+batch_size]
                logger.info(f"▶️ Processing batch {i//batch_size + 1} size={len(batch)}")
                async def _change_with_sem(acc):
                    async with sem:
                        return await safe_change_first_name(acc, spam_config, new_first_name, remove_client_from_pool)

                tasks = [_change_with_sem(acc) for acc in batch]
                results = await asyncio.gather(*tasks, return_exceptions=False)
                successes = sum(1 for r in results if r is True)
                total_changed += successes
                logger.info(f"✅ Batch done — changed: {successes}/{len(batch)} | total_changed={total_changed}")
                await asyncio.sleep(base_delay)

    except asyncio.CancelledError:
        logger.info("🛑 run_spammer cancelled.")
        raise
    except Exception as e:
        logger.exception(f"💥 Unhandled error in run_spammer: {type(e).__name__} - {e}")
    finally:
        logger.info("🛑 Spammer async stopped gracefully.")
        logger.info(f"📈 Total profiles changed: {total_changed}")

# ================== compatibility wrapper: keeps API expected by core_handler ==================
class SpammerThreadingRunner:
    def __init__(self, spam_config: Dict[str, Any], remove_client_from_pool: Callable[[str], None]):
        self.spam_config = spam_config or {}
        self.remove_client_from_pool = remove_client_from_pool
        self._task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self):
        # must be called from within running asyncio event loop (pyrogram handler context)
        if self._task and not self._task.done():
            logger.info("ℹ️ Spammer already running.")
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("SpammerThreadingRunner.start() must be called from an async context with running loop.")

        self._loop = loop
        self.spam_config["run"] = True
        self._task = loop.create_task(run_spammer(self.spam_config, getattr(client_manager, "remove_client_from_pool", lambda x: None)))
        logger.info("▶️ SpammerThreadingRunner started (async task created).")

    def stop(self):
        logger.info("🧩 Stop requested for SpammerThreadingRunner.")
        try:
            self.spam_config["run"] = False
        except Exception:
            pass

        if self._task and not self._task.done():
            try:
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
            except Exception:
                logger.exception("Error while cancelling spammer task.")

# ================== optional helper singleton API like previous code ==================
_spammer_runner_singleton: Optional[SpammerThreadingRunner] = None

def start_spammer_thread(spam_config: Dict[str, Any], remove_client_from_pool: Callable[[str], None]) -> SpammerThreadingRunner:
    global _spammer_runner_singleton
    if _spammer_runner_singleton and _spammer_runner_singleton._task and not _spammer_runner_singleton._task.done():
        logger.info("ℹ️ Spammer already running (singleton).")
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
        logger.info("✅ Spammer stopped (singleton cleared).")
    else:
        logger.info("ℹ️ No running spammer to stop.")
