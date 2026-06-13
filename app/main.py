from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import ExifTags, Image

from app.thumbnails import get_or_create_thumbnail

app = FastAPI(title="Photo Gallery")

PHOTOS_DIR = Path("photos")
THUMBNAILS_DIR = Path(".thumbnails")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tiff"}

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def _safe_photo_path(photo_path: str) -> Path:
    try:
        path = (PHOTOS_DIR / photo_path).resolve()
        photos_root = PHOTOS_DIR.resolve()
        relative_path = path.relative_to(photos_root)
    except ValueError:
        raise HTTPException(status_code=400)

    if _is_hidden(relative_path):
        raise HTTPException(status_code=404)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404)
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=404)

    return path


def _photo_created_at(path: Path) -> float:
    exif_timestamp = _exif_created_at(path)
    if exif_timestamp is not None:
        return exif_timestamp
    return path.stat().st_mtime


def _exif_created_at(path: Path) -> float | None:
    try:
        with Image.open(path) as img:
            exif = img.getexif()
    except Exception:
        return None

    if not exif:
        return None

    date_tags = {"DateTimeOriginal", "DateTimeDigitized", "DateTime"}
    tag_ids = {
        tag_id
        for tag_id, tag_name in ExifTags.TAGS.items()
        if tag_name in date_tags
    }

    for tag_id in tag_ids:
        value = exif.get(tag_id)
        if not value:
            continue
        parsed = _parse_exif_datetime(str(value))
        if parsed is not None:
            return parsed

    return None


def _parse_exif_datetime(value: str) -> float | None:
    from datetime import datetime

    try:
        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S").timestamp()
    except ValueError:
        return None


def get_portfolio_photos() -> list[dict]:
    if not PHOTOS_DIR.exists():
        return []

    photos = []
    for path in PHOTOS_DIR.rglob("*"):
        relative_path = path.relative_to(PHOTOS_DIR)
        if not path.is_file() or _is_hidden(relative_path):
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        created_at = _photo_created_at(path)
        photo_path = relative_path.as_posix()
        url_path = quote(relative_path.as_posix(), safe="/")
        photos.append({
            "id": hashlib.sha1(photo_path.encode("utf-8")).hexdigest()[:12],
            "path": photo_path,
            "url_path": url_path,
            "created_at": created_at,
        })

    return sorted(
        photos,
        key=lambda photo: (-photo["created_at"], photo["path"]),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def index(request: Request):
    photos = get_portfolio_photos()
    photo_data = [
        {"id": photo["id"], "url_path": photo["url_path"]}
        for photo in photos
    ]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "photos": photos,
            "photos_json": json.dumps(photo_data),
            "count": len(photos),
        },
    )


@app.get("/photos/{photo_path:path}")
async def serve_photo(photo_path: str):
    path = _safe_photo_path(photo_path)
    return FileResponse(path)


@app.get("/thumbnails/{photo_path:path}")
async def serve_thumbnail(photo_path: str):
    original = _safe_photo_path(photo_path)
    relative_path = original.relative_to(PHOTOS_DIR.resolve())
    thumb_path = THUMBNAILS_DIR / relative_path.with_suffix(".jpg")

    thumb = get_or_create_thumbnail(
        original,
        thumb_path=thumb_path,
    )
    return FileResponse(thumb, media_type="image/jpeg")
