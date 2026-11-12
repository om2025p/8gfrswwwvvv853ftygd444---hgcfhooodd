"""HTTP server for Download Shield.

Runs the Telegram clients and the FastAPI app on one asyncio loop so the user
session is never opened twice (Telegram rejects that with AUTH_KEY_DUPLICATED).
"""

import asyncio
import glob
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)

SERVER_TOKEN = os.environ.get("SERVER_TOKEN", "").strip()
PORT = int(os.environ.get("PORT", "8080"))

app = FastAPI(title="Download Shield Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_state = {
    "status": "idle",
    "job": None,
    "message": "",
    "started_at": None,
    "finished_at": None,
}
_job_lock = asyncio.Lock()
_job_task = None
_clients_ready = False

_log_lines = []
_log_counter = 0
_log_lock = threading.Lock()


class _Tee:
    """Mirror stdout/stderr into a ring buffer the web app can poll."""

    def __init__(self, stream):
        self._stream = stream

    def write(self, data):
        try:
            self._stream.write(data)
        except Exception:
            pass
        if data:
            global _log_counter
            with _log_lock:
                for line in str(data).splitlines():
                    if line.strip():
                        _log_lines.append({"i": _log_counter, "t": line})
                        _log_counter += 1
                if len(_log_lines) > 3000:
                    del _log_lines[:-3000]
        return len(data)

    def flush(self):
        try:
            self._stream.flush()
        except Exception:
            pass

    def isatty(self):
        return False


def _now():
    return datetime.now(timezone.utc).isoformat()


def _check(token):
    if not SERVER_TOKEN:
        raise HTTPException(status_code=503, detail="SERVER_TOKEN is not configured")
    if token != SERVER_TOKEN:
        raise HTTPException(status_code=401, detail="invalid token")


@app.get("/health")
async def health():
    return {
        "ok": True,
        "status": _state["status"],
        "job": _state["job"],
        "clients": _clients_ready,
    }


@app.get("/api/status")
async def status(x_auth_token: str = Header(default="")):
    _check(x_auth_token)
    return {"ok": True, **_state}


@app.get("/api/logs")
async def logs(since: int = 0, x_auth_token: str = Header(default="")):
    _check(x_auth_token)
    with _log_lock:
        lines = [line for line in _log_lines if line["i"] >= since]
        total = _log_counter
    return {"ok": True, "next": total, "lines": lines}


@app.post("/api/download")
async def api_download(payload: dict, x_auth_token: str = Header(default="")):
    _check(x_auth_token)
    return _start_job("download", payload)


@app.post("/api/gallery")
async def api_gallery(payload: dict, x_auth_token: str = Header(default="")):
    _check(x_auth_token)
    return _start_job("gallery", payload)


@app.post("/api/zip")
async def api_zip(payload: dict, x_auth_token: str = Header(default="")):
    _check(x_auth_token)
    return _start_job("zip", payload)


@app.post("/api/cancel")
async def api_cancel(x_auth_token: str = Header(default="")):
    _check(x_auth_token)
    if _job_task and not _job_task.done():
        _job_task.cancel()
        _state.update(status="cancelled", message="لغو شد", finished_at=_now())
        return {"ok": True}
    return {"ok": False, "error": "کاری در حال اجرا نیست"}


def _start_job(job, payload):
    global _job_task
    if not _clients_ready:
        return JSONResponse(
            status_code=503, content={"ok": False, "error": "کلاینت تلگرام آماده نیست"}
        )
    if _job_task and not _job_task.done():
        return JSONResponse(
            status_code=409, content={"ok": False, "error": "یک کار دیگر در حال اجراست"}
        )
    _job_task = asyncio.create_task(_run_job(job, payload))
    return {"ok": True, "job": job, "status": "running"}


_JOB_ENV_KEYS = (
    "TELEGRAM_LINK",
    "GALLERY_URL",
    "ZIP_URL",
    "IS_GALLERY_MODE",
    "START_PART",
    "START_PAGE",
    "SORT_MODE",
    "CUSTOM_DB_BASE",
    "IS_DISCOVERY_MODE",
)


def _reset_job_env():
    for key in _JOB_ENV_KEYS:
        os.environ.pop(key, None)


async def _run_job(job, payload):
    async with _job_lock:
        _state.update(
            status="running",
            job=job,
            message="در حال اجرا",
            started_at=_now(),
            finished_at=None,
        )
        _reset_job_env()
        try:
            if job == "download":
                os.environ["TELEGRAM_LINK"] = str(payload.get("url", ""))
                os.environ["TARGET_CHANNEL"] = str(
                    payload.get("targetChannel") or "-1003757877147"
                )
                import download_single

                await download_single.main_download()
            elif job == "gallery":
                url = str(payload.get("url", ""))
                os.environ["TELEGRAM_LINK"] = url
                os.environ["GALLERY_URL"] = url
                os.environ["IS_GALLERY_MODE"] = "true"
                os.environ["START_PART"] = str(payload.get("startPart") or "1")
                os.environ["SORT_MODE"] = str(payload.get("sortMode") or "newest")
                os.environ["CUSTOM_DB_BASE"] = str(payload.get("customDb") or "")
                os.environ["IS_DISCOVERY_MODE"] = (
                    "true" if payload.get("discovery") else "false"
                )
                os.environ["TARGET_CHANNEL"] = str(
                    payload.get("targetChannel") or "-1004389912148"
                )
                import download_single

                await download_single.main_download()
            elif job == "zip":
                url = str(payload.get("url", ""))
                os.environ["ZIP_URL"] = url
                os.environ["TELEGRAM_LINK"] = url
                os.environ["TARGET_CHANNEL"] = str(
                    payload.get("targetChannel") or "-1004498823531"
                )
                import zip_extractor

                await zip_extractor.main()
            else:
                raise ValueError("unknown job: " + str(job))

            _state.update(status="done", message="تمام شد ✅", finished_at=_now())
        except asyncio.CancelledError:
            _state.update(status="cancelled", message="لغو شد", finished_at=_now())
        except Exception as exc:
            _state.update(status="error", message=str(exc), finished_at=_now())
            print(f"[server] job {job} failed: {exc}")
        finally:
            _reset_job_env()


def _make_start_idempotent(client):
    """Engines call start() again; a second call on a live client must not fail."""
    if not hasattr(client, "start"):
        return
    original = client.start

    async def _start(*args, **kwargs):
        if getattr(client, "is_connected", False):
            return client
        result = original(*args, **kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        return result

    client.start = _start


async def _connect_clients():
    global _clients_ready
    import main
    from main import bot, userbot, Bot, BOT_TOKEN

    try:
        await bot.connect()
        if not await bot.is_user_authorized():
            await bot.sign_in(bot_token=BOT_TOKEN)
        print("[server] telethon bot connected")
    except Exception as exc:
        print(f"[server] telethon bot connect failed: {exc}")

    try:
        await userbot.start()
        print("[server] pyrogram userbot connected")
    except Exception as exc:
        print(f"[server] userbot connect failed: {exc}")

    try:
        await Bot.start()
        print("[server] pyrogram bot connected")
    except Exception as exc:
        print(f"[server] pyrogram bot connect failed: {exc}")

    _make_start_idempotent(userbot)
    _make_start_idempotent(Bot)

    try:
        from main.utils import load_plugins

        for path in sorted(glob.glob(str(BASE_DIR / "main" / "plugins" / "*.py"))):
            name = Path(path).stem
            if name.startswith("_"):
                continue
            load_plugins(name)
        print("[server] plugins loaded")
    except Exception as exc:
        print(f"[server] plugin load failed: {exc}")

    _clients_ready = True


async def _serve():
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def _main():
    sys.stdout = _Tee(sys.stdout)
    sys.stderr = _Tee(sys.stderr)
    try:
        await _connect_clients()
    except Exception as exc:
        print(f"[server] startup failed: {exc}")
    await _serve()


if __name__ == "__main__":
    asyncio.run(_main())
