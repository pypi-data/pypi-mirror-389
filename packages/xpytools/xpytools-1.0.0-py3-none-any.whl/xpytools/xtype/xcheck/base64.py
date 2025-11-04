import base64
import re

# precompiled regex: only base64-safe chars and padding
_BASE64_RE = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")


def is_base64(data: str) -> bool:
    """
    Heuristically xcheck if a string is valid Base64-encoded data.
    Returns True only if:
      • it's a str of reasonable length,
      • matches base64 charset,
      • and decodes successfully without error.
    """
    if not isinstance(data, str) or len(data) < 16:  # short strings are rarely base64 images
        return False

    # strip any data URI prefix
    if "," in data and data.strip().startswith("data:"):
        data = data.split(",", 1)[1]

    data = data.strip()

    # must be multiple of 4 chars (Base64 requirement)
    if len(data) % 4 != 0:
        return False

    # must match base64 charset (A–Z, a–z, 0–9, +, /, =)
    if not _BASE64_RE.match(data):
        return False

    # try decode / re-encode consistency xcheck
    try:
        decoded = base64.b64decode(data, validate=True)
        # re-encode and see if it matches (ignoring trailing padding differences)
        reencoded = base64.b64encode(decoded).decode().rstrip("=")
        return data.rstrip("=") == reencoded
    except Exception:
        return False
