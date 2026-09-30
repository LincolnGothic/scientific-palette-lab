"""Configuration for a single private workspace behind an HTTPS reverse proxy."""

import base64
import binascii
import hashlib
import hmac
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class WebAccess:
    external_url: str = ""
    username: str = "researcher"
    password: str = ""

    def validate(self, host):
        if self.external_url:
            url = urlsplit(self.external_url)
            if (url.scheme != "https" or not url.hostname or url.username or url.password
                    or url.path not in ("", "/") or url.query or url.fragment):
                raise ValueError("PALETTE_EXTERNAL_URL must be an HTTPS site URL without a path or credentials.")
        if host not in ("127.0.0.1", "localhost"):
            if not self.external_url or len(self.password) < 16:
                raise ValueError("Hosted mode requires an HTTPS external URL and PALETTE_WEB_PASSWORD (at least 16 characters).")
        if self.password and (not self.username or ":" in self.username):
            raise ValueError("PALETTE_WEB_USERNAME must be nonempty and must not contain a colon.")
        return self

    def permitted(self, host, origin, port):
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        origins = {f"http://{h}" for h in hosts}
        if self.external_url:
            url = urlsplit(self.external_url)
            hosts.add(url.netloc.lower())
            origins.add(f"{url.scheme}://{url.netloc}")
        return host.lower() in hosts and (not origin or origin in origins)

    def authenticated(self, authorization):
        if not self.password:
            return True
        try:
            scheme, token = (authorization or "").split(" ", 1)
            if scheme.lower() != "basic" or len(token) > 8192:
                return False
            supplied = base64.b64decode(token, validate=True)
        except (ValueError, binascii.Error):
            return False
        expected = f"{self.username}:{self.password}".encode("utf-8")
        return hmac.compare_digest(hashlib.sha256(supplied).digest(), hashlib.sha256(expected).digest())
