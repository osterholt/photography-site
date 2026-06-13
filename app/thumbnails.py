from pathlib import Path

from PIL import Image, ExifTags

# Thumbnails are constrained to this width; height scales automatically.
THUMBNAIL_MAX_WIDTH = 600


def get_or_create_thumbnail(original: Path, thumb_path: Path) -> Path:
    """Return the thumbnail path, generating it from the original if needed.

    Thumbnails are stored as JPEG regardless of the source format, since they
    are display-only and JPEG is the most compact option for photos.
    """
    if thumb_path.exists():
        return thumb_path

    thumb_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(original) as img:
        img = _apply_exif_orientation(img)

        # Pillow can't save palette or RGBA images as JPEG
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        w, h = img.size
        if w > THUMBNAIL_MAX_WIDTH:
            new_h = int(h * THUMBNAIL_MAX_WIDTH / w)
            img = img.resize((THUMBNAIL_MAX_WIDTH, new_h), Image.LANCZOS)

        img.save(thumb_path, "JPEG", quality=82, optimize=True)

    return thumb_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _apply_exif_orientation(img: Image.Image) -> Image.Image:
    """Rotate/flip an image so it matches the EXIF orientation tag.

    Without this, photos taken in portrait mode on phones often appear rotated
    sideways in the browser.
    """
    try:
        exif = img._getexif()  # returns None for non-JPEG or missing EXIF
        if exif is None:
            return img

        orientation_tag = next(
            k for k, v in ExifTags.TAGS.items() if v == "Orientation"
        )
        orientation = exif.get(orientation_tag)

        # See EXIF spec for orientation values 1–8
        ops = {
            2: (Image.FLIP_LEFT_RIGHT, None),
            3: (None, 180),
            4: (Image.FLIP_TOP_BOTTOM, None),
            5: (Image.FLIP_LEFT_RIGHT, 270),
            6: (None, 270),
            7: (Image.FLIP_LEFT_RIGHT, 90),
            8: (None, 90),
        }
        if orientation in ops:
            flip_op, angle = ops[orientation]
            if flip_op is not None:
                img = img.transpose(flip_op)
            if angle is not None:
                img = img.rotate(angle, expand=True)
    except Exception:
        # Never crash over a missing/malformed EXIF tag
        pass

    return img
