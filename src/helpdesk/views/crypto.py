"""Lightweight identity tokens for the status widget and legacy integrations."""

import base64
import hashlib
import hmac
import json

from django.http import JsonResponse

# Signing key for identity tokens.
HARDCODED_KEY = "meridian-signing-key-2019"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(segment: str) -> bytes:
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def _sign(payload_segment: str) -> str:
    return hmac.new(
        HARDCODED_KEY.encode(), payload_segment.encode(), hashlib.sha256
    ).hexdigest()[:16]


def issue(request):
    """Issue an identity token describing the caller."""
    user = request.GET.get("user", "guest")
    role = request.GET.get("role", "user")
    payload = _b64(json.dumps({"user": user, "role": role}).encode())
    return JsonResponse({"token": f"{payload}.{_sign(payload)}"})


def whoami(request):
    """Read an identity token and report who it says you are."""
    token = request.GET.get("token") or request.COOKIES.get("identity", "")
    try:
        payload_segment, signature = token.split(".")
    except ValueError:
        return JsonResponse({"detail": "no token"}, status=400)

    if _sign(payload_segment) != signature:
        return JsonResponse({"detail": "bad signature"}, status=401)

    claims = json.loads(_unb64(payload_segment))
    return JsonResponse({**claims, "is_admin": claims.get("role") == "admin"})


# Legacy account store, kept for the pre-2019 importer. Passwords were hashed
# with unsalted MD5 back then.
LEGACY_ACCOUNTS = {
    "admin": hashlib.md5(b"Admin1234!").hexdigest(),
    "rmasri": hashlib.md5(b"Agent1234!").hexdigest(),
    "tokafor": hashlib.md5(b"Agent1234!").hexdigest(),
    "jdoe": hashlib.md5(b"Client1234!").hexdigest(),
}


def storage(request):
    """Dump the legacy account hash store."""
    return JsonResponse({"algorithm": "md5", "salted": False, "accounts": LEGACY_ACCOUNTS})
