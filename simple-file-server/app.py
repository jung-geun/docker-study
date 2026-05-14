import copy
import html
import logging
from logging.config import dictConfig
import os
from pathlib import Path
from typing import List
from urllib.parse import quote

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

app = FastAPI(title="Simple File Server")

PORT = int(os.getenv("PORT", "3001"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/var/uploads")).resolve()
LOG_FILE = Path(os.getenv("LOG_PATH", "/var/log/app.log")).resolve()

# Ensure the upload directory exists before any request handling.
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
try:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _build_logging_config() -> dict:
        """Return a logging configuration that mirrors uvicorn defaults plus a file sink."""
        try:
            from uvicorn.config import LOGGING_CONFIG as uvicorn_logging_config
        except ImportError:  # pragma: no cover - uvicorn should be present, but guard defensively
            formatter = {
                "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
            }
            return {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {"file": formatter},
                "handlers": {
                    "file": {
                        "class": "logging.handlers.WatchedFileHandler",
                        "filename": str(LOG_FILE),
                        "formatter": "file",
                        "encoding": "utf-8",
                    }
                },
                "root": {"level": "INFO", "handlers": ["file"]},
            }

        config = copy.deepcopy(uvicorn_logging_config)
        config.setdefault("handlers", {})
        config.setdefault("formatters", {})

        config["formatters"]["file"] = {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s %(name)s %(message)s",
            "use_colors": False,
        }
        config["handlers"]["file"] = {
            "class": "logging.handlers.WatchedFileHandler",
            "filename": str(LOG_FILE),
            "formatter": "file",
            "encoding": "utf-8",
        }

        for logger_name, default_handler in (
            ("uvicorn", "default"),
            ("uvicorn.error", "default"),
            ("uvicorn.access", "access"),
        ):
            logger_cfg = config.setdefault("loggers", {}).setdefault(logger_name, {})
            handlers = logger_cfg.get("handlers") or [default_handler]
            if "file" not in handlers:
                handlers.append("file")
            logger_cfg["handlers"] = handlers

        config["loggers"].setdefault(
            "fastapi",
            {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False,
            },
        )

        default_handlers = []
        if "default" in config.get("handlers", {}):
            default_handlers.append("default")

        # Ensure application logs also reach the file handler.
        config["root"] = {
            "level": "INFO",
            "handlers": default_handlers + ["file"],
        }

        return config


    LOGGING_CONFIG = _build_logging_config()

    # Apply the logging configuration immediately so any import-time logging is captured.
    dictConfig(LOGGING_CONFIG)
    
    try:
        import uvicorn.config as _uvicorn_config

        _uvicorn_config.LOGGING_CONFIG = LOGGING_CONFIG
    except ImportError:  # pragma: no cover - uvicorn should be installed already
        pass
    
except Exception:  # pragma: no cover - defensive logging path
    pass



def _safe_filename(filename: str) -> str:
    """Return a baseline filename to prevent path traversal."""
    candidate = os.path.basename(filename)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is invalid.")
    return candidate


def _list_uploaded_files() -> List[Path]:
    """Return a sorted list of uploaded files."""
    return sorted((file for file in UPLOAD_DIR.iterdir() if file.is_file()), key=lambda item: item.name.lower())


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    files = _list_uploaded_files()
    if files:
        items = "\n".join(
            f'<li><a href="/download/{quote(file.name)}">{html.escape(file.name)}</a>'
            f" ({file.stat().st_size} bytes)</li>"
            for file in files
        )
    else:
        items = "<li>No files uploaded yet.</li>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>FastAPI File Server</title>
    <style>
        body {{ font-family: sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }}
        form {{ margin-bottom: 2rem; }}
        ul {{ padding-left: 1.5rem; }}
        li {{ margin: 0.5rem 0; }}
        code {{ background: #f4f4f4; padding: 0.2rem 0.4rem; border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>FastAPI File Server</h1>
    <p>Files are stored at <code>{html.escape(str(UPLOAD_DIR))}</code>. Listening on port <strong>{PORT}</strong>.</p>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <label for="file">Upload file:</label>
        <input id="file" name="file" type="file" required>
        <button type="submit">Upload</button>
    </form>
    <h2>Uploaded Files</h2>
    <ul>
        {items}
    </ul>
</body>
</html>"""


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> RedirectResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file selected.")

    safe_name = _safe_filename(file.filename)
    destination = UPLOAD_DIR / safe_name

    try:
        content = await file.read()
        destination.write_bytes(content)
    except Exception as exc:  # pragma: no cover - defensive logging path
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {exc}") from exc

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/download/{filename}")
async def download_file(filename: str) -> FileResponse:
    safe_name = _safe_filename(filename)
    file_path = UPLOAD_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    return FileResponse(path=file_path, filename=safe_name)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/files")
async def list_files() -> List[dict]:
    return [
        {"name": file.name, "size": file.stat().st_size}
        for file in _list_uploaded_files()
    ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=PORT)
