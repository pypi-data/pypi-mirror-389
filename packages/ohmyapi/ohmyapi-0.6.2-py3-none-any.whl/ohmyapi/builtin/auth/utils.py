import base64
import hashlib
import hmac

import settings

SECRET_KEY = getattr(settings, "SECRET_KEY", "OhMyAPI Secret Key")


def hmac_hash(data: str) -> str:
    digest = hmac.new(
        SECRET_KEY.encode("UTF-8"),
        data.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8")

