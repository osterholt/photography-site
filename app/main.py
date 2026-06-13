import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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

def _is_safe(name: str) -> bool:
    """Reject any path segment that tries to escape the photos directory."""
    return ".." not in name and "/" not in name and "\\" not in name


def get_albums() -> list[dict]:
    if not PHOTOS_DIR.exists():
        return []
    albums = []
    for item in sorted(PHOTOS_DIR.iterdir()):
        if not item.is_dir() or item.name.startswith("."):
            continue
        photos = sorted(
            p for p in item.iterdir()
            if p.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if photos:
            albums.append({
                "name": item.name,
                "slug": item.name,
                "count": len(photos),
                "cover_name": photos[0].name,   # first photo as cover
                "display_name": item.name.replace("-", " ").replace("_", " ").title(),
            })
    return albums


def get_photos_in_album(slug: str) -> list[Path] | None:
    album_path = PHOTOS_DIR / slug
    if not album_path.exists() or not album_path.is_dir():
        return None
    return sorted(
        p for p in album_path.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "albums": get_albums()},
    )


@app.get("/album/{slug}")
async def album(request: Request, slug: str):
    if not _is_safe(slug):
        raise HTTPException(status_code=400)

    photos = get_photos_in_album(slug)
    if photos is None:
        raise HTTPException(status_code=404, detail="Album not found")

    photo_names = [p.name for p in photos]
    return templates.TemplateResponse(
        "album.html",
        {
            "request": request,
            "album_name": slug.replace("-", " ").replace("_", " ").title(),
            "slug": slug,
            "photos": photo_names,
            "photos_json": json.dumps(photo_names),
            "count": len(photos),
        },
    )


@app.get("/photos/{album}/{filename}")
async def serve_photo(album: str, filename: str):
    if not _is_safe(album) or not _is_safe(filename):
        raise HTTPException(status_code=400)

    path = PHOTOS_DIR / album / filename
    if not path.exists() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=404)

    return FileResponse(path)


@app.get("/thumbnails/{album}/{filename}")
async def serve_thumbnail(album: str, filename: str):
    if not _is_safe(album) or not _is_safe(filename):
        raise HTTPException(status_code=400)

    original = PHOTOS_DIR / album / filename
    if not original.exists() or original.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=404)

    thumb = get_or_create_thumbnail(
        original,
        thumb_path=THUMBNAILS_DIR / album / (Path(filename).stem + ".jpg"),
    )
    return FileResponse(thumb, media_type="image/jpeg")
