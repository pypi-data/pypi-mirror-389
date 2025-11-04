from __future__ import annotations

from io import BytesIO
from typing import Optional

from ...xdeco import requireModules

try:
    from PIL import Image
    from PIL.Image import Resampling
except ImportError:
    Image = None
    Resampling = None


@requireModules(['PIL'], exc_raise=True)
def create_thumbnail(
        image_data: bytes,
        size: tuple[int, int] = (300, 300),
        format: str = "PNG",
        ) -> bytes:
    """
    Create a thumbnail from img bytes and return as bytes.
    Keeps aspect ratio, converts to RGB, and uses high-quality downsampling.
    """
    if not Image:
        raise ImportError("Pillow (PIL) is required for img operations.")

    image = Image.open(BytesIO(image_data))
    if image.mode != "RGB":
        image = image.convert("RGB")

    image.thumbnail(size, Resampling.LANCZOS)
    buffer = BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()


@requireModules(['PIL'], exc_raise=True)
def resize(
        image_data: bytes,
        size: tuple[int, int],
        format: Optional[str] = None,
        keep_aspect: bool = True,
        ) -> bytes:
    """
    Resize img to a specific size. Optionally keeps aspect ratio.
    """
    if not Image:
        raise ImportError("Pillow (PIL) is required for resize_image().")

    img = Image.open(BytesIO(image_data))
    if img.mode != "RGB":
        img = img.convert("RGB")

    if keep_aspect:
        img.thumbnail(size, Resampling.LANCZOS)
    else:
        img = img.resize(size, Resampling.LANCZOS)

    buf = BytesIO()
    fmt = format or img.format or "PNG"
    img.save(buf, format=fmt)
    return buf.getvalue()
