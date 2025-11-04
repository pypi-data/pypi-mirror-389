from __future__ import annotations

import base64
from io import BytesIO

from .load import Image, _load_from_base64
from ...xdeco import requireModules


@requireModules(["PIL"], exc_raise=True)
def to_bytes(img: "Image.Image", format: str = "PNG") -> bytes:
    buf = BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


@requireModules(["PIL"], exc_raise=True)
def from_bytes(data: bytes) -> "Image.Image":
    return Image.open(BytesIO(data))


@requireModules(["PIL"], exc_raise=True)
def from_base64(b64_str: str) -> "Image.Image":
    return from_bytes(_load_from_base64(b64_str))


@requireModules(["PIL"], exc_raise=True)
def to_base64(img: "Image.Image", format: str = "PNG") -> str:
    return base64.b64encode(to_bytes(img, format)).decode("utf-8")


def base64_to_bytes(b64_str: str) -> bytes:
    return _load_from_base64(b64_str)
