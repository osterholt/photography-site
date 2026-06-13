# Photo Gallery

A self-hosted photography portfolio built with FastAPI + Pillow. Drop photos
anywhere under `photos/`, get one date-sorted masonry grid and lightbox out —
no database, no config.

## Project layout

```
photo-gallery/
├── app/
│   ├── main.py          # FastAPI routes
│   ├── thumbnails.py    # Pillow thumbnail + EXIF auto-rotation logic
│   └── templates/       # Jinja2 HTML templates
│       ├── base.html
│       └── index.html   # photo masonry grid + lightbox
├── static/
│   └── style.css        # all styling
├── photos/              # ← put your photos here
├── .thumbnails/         # auto-generated, git-ignored
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Adding photos

All supported images under `photos/` are shown in one portfolio, sorted newest
to oldest. Camera EXIF capture time is used when available, with filesystem
modified time as the fallback. Subfolders are fine for storage, but they do not
create albums in the UI.

```
photos/
├── iceland-2024/
│   ├── DSC_0001.jpg
│   └── DSC_0002.jpg
└── street-photography/
    └── IMG_3456.jpg
```

Thumbnails are generated on first request and cached in `.thumbnails/`, using
the same relative paths as `photos/`.
Supported formats: **JPG, JPEG, PNG, WEBP, GIF, TIFF**.

---

## Local development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run with hot-reload
uvicorn app.main:app --reload

# Open http://localhost:8000
```

---

## Docker (production / home server)

```bash
# Build and start
docker compose up --build -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

The `photos/` folder and `.thumbnails/` are mounted as volumes, so your
data lives outside the container and survives rebuilds.

### Putting it behind a reverse proxy (Nginx / Caddy)

Point your reverse proxy at `http://localhost:8000`.

**Nginx example:**
```nginx
server {
    listen 80;
    server_name photos.yourdomain.com;

    location / {
        proxy_pass         http://localhost:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        # Increase for large original photo downloads
        proxy_read_timeout 120s;
    }
}
```

---

## Customisation

| What | Where |
|---|---|
| Site name | `app/templates/base.html` → `.site-name` |
| Thumbnail size | `app/thumbnails.py` → `THUMBNAIL_MAX_WIDTH` |
| Colour palette | `static/style.css` → `:root` tokens |
| Columns on desktop | `static/style.css` → `.photo-grid { columns: N }` |

## Regenerating thumbnails

Delete `.thumbnails/` and restart — they'll be recreated on demand.

```bash
rm -rf .thumbnails/
docker compose restart   # or uvicorn restart for local dev
```
