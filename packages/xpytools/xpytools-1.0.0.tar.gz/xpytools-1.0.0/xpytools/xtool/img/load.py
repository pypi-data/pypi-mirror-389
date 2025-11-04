#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
xpytools.xtool.imgo
-----------------------
Unified lightweight I/O helpers for images.

    • load from path, URL, or base64
    • base64 ↔ Pillow Image ↔ bytes
    • save img locally
"""

from __future__ import annotations, annotations

import base64
from pathlib import Path
from typing import Union, Literal

from ...xdeco import requireModules
from ...xtype.xcheck import is_base64

try:
    import requests
except ImportError:
    requests = None

try:
    from PIL import Image
except ImportError:
    Image = None


# ---------------------------------------------------------------------------
# Base loaders
# ---------------------------------------------------------------------------

@requireModules(["requests"], exc_raise=True)
def _load_from_url(url: str, timeout: int = 20) -> bytes:
    """Download img from HTTP(S) URL and return bytes."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def _load_from_path(path: Union[str, Path]) -> bytes:
    """Read img bytes from local path."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    return path.read_bytes()


def _load_from_base64(data: str) -> bytes:
    """Decode base64 string (with or without data URI prefix)."""
    if "," in data and data.strip().startswith("data:"):
        data = data.split(",", 1)[1]
    return base64.b64decode(data)


@requireModules(["PIL"], exc_raise=False)
def load(
        src: Union[str, Path, bytes],
        rtype: Literal["bytes", "base64", "pil.img"] = "bytes",
        timeout: int = 20,
        ) -> Union[bytes, str, "Image.Image"]:
    """
    Load an img from any source (file path, URL, base64, bytes)
    and return the requested representation.

    Parameters
    ----------
    src : str | Path | bytes
        Image source (local path, URL, base64 string, or raw bytes).
    rtype : {'bytes', 'base64', 'pil.img'}, default='bytes'
        Return type.
    timeout : int, default=20
        Timeout for URL downloads.

    Returns
    -------
    bytes | str | Image.Image
        Image data in desired representation.
    """
    # --- Normalize to bytes --------------------------------------------------
    if isinstance(src, (bytes, bytearray)):
        img_bytes = bytes(src)
    elif isinstance(src, str) and src.startswith(("http://", "https://")):
        img_bytes = _load_from_url(src, timeout)
    elif isinstance(src, str) and is_base64(src):
        from .conversions import base64_to_bytes
        img_bytes = base64_to_bytes(src)
    elif isinstance(src, Path):
        img_bytes = _load_from_path(src)
    elif isinstance(src, str) and '/' in src or '.' in src:
        img_bytes = _load_from_path(src)
    else:
        raise ValueError(f"Unsupported img source type: {type(src)}")

    # --- Delegate to converters ---------------------------------------------
    if rtype == "bytes":
        return img_bytes
    if rtype == "base64":
        return base64.b64encode(img_bytes).decode("utf-8")
    if rtype == "pil.img":
        if not Image:
            raise ImportError("Pillow not installed; cannot return PIL Image.")
        from .conversions import from_bytes
        return from_bytes(img_bytes)

    raise ValueError(f"Invalid rtype: {rtype!r} (expected 'bytes', 'base64', or 'pil.img').")
