# Photo Gallery

A self-hosted photography portfolio built with FastAPI + Pillow. Drop a folder
of photos in, get a masonry grid and lightbox out — no database, no config.

## Project layout

```
photo-gallery/
├── app/
│   ├── main.py          # FastAPI routes
│   ├── thumbnails.py    # Pillow thumbnail + EXIF auto-rotation logic
│   └── templates/       # Jinja2 HTML templates
│       ├── base.html
│       ├── index.html   # album grid
│       └── album.html   # photo masonry grid + lightbox
├── static/
│   └── style.css        # all styling
├── photos/              # ← put your photo folders here
├── .thumbnails/         # auto-generated, git-ignored
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Adding photos

Each subfolder inside `photos/` becomes an album:

```
photos/
├── iceland-2024/
│   ├── DSC_0001.jpg
│   └── DSC_0002.jpg
└── street-photography/
    └── IMG_3456.jpg
```

Thumbnails are generated on first request and cached in `.thumbnails/`.
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
