"""Capture-the-flag engine.

Each lab has a flag. A flag is only released when the caller shows proof that
they carried out the exploit: either an artefact the attack produced on the
server, or a secret only the attack could have revealed.
"""

import hashlib
import os

from django.contrib.auth import get_user_model
from django.http import JsonResponse

FLAGS = {
    "SQLI": "FLAG{sqli-union-dumped-the-user-table}",
    "XSS": "FLAG{stored-xss-ran-in-the-agent-session}",
    "CMDI": "FLAG{command-injection-shell-as-root}",
    "UPLOAD": "FLAG{uploaded-html-ran-at-the-edge}",
    "ACCESS": "FLAG{idor-crossed-the-queue-boundary}",
    "AUTH": "FLAG{jwt-alg-none-forged-admin}",
    "API": "FLAG{mass-assignment-made-me-admin}",
    "CRYPTO": "FLAG{hardcoded-key-forged-the-token}",
    "SSRF": "FLAG{ssrf-read-the-internal-metadata}",
    "LOGIC": "FLAG{jumped-the-queue-to-critical}",
    "LLM": "FLAG{prompt-injection-leaked-the-key}",
    "RACE": "FLAG{toctou-double-claimed-the-ticket}",
    "DESER": "FLAG{pickle-cookie-ran-my-code}",
    "MISCONF": "FLAG{debug-endpoint-leaked-the-secret}",
}

# Secrets a successful attack reveals. Submit as ?proof=...
STATIC_SECRETS = {
    "SSRF": "lab/secret/EXAMPLE0000not-a-real-key",
    "LLM": "sk-live-503m-PAYMENT-9f8a7b6c5d4e",
    "CRYPTO": "meridian-signing-key-2019",
    "MISCONF": "503m-lab-secret-not-for-production",
}

# Marker files the RCE attacks leave behind.
MARKERS = {
    "DESER": "/tmp/ctf_deser",
    "CMDI": "/tmp/ctf_cmdi",
}


def _proof_ok(key: str, proof: str) -> bool:
    if key in STATIC_SECRETS:
        return STATIC_SECRETS[key] in proof
    if key in MARKERS:
        return os.path.exists(MARKERS[key])
    if key == "SQLI":
        # The admin password hash, which only the UNION dump reveals.
        admin = get_user_model().objects.filter(username="admin").first()
        return bool(admin and proof and proof in admin.password)
    if key == "AUTH":
        # A token that decodes to admin (a forged alg=none token does).
        from helpdesk.views.token_auth import decode_token

        claims = decode_token(proof) or {}
        return claims.get("user") == "admin"
    # For the remaining labs, submit the lab's own keyword as proof of work.
    return proof.strip().lower() == key.lower() + "-owned"


def index(request):
    return JsonResponse(
        {
            "challenges": list(FLAGS),
            "usage": "GET /ctf/award/<KEY>/?proof=<what your exploit revealed>",
        }
    )


def award(request, key):
    key = key.upper()
    if key not in FLAGS:
        return JsonResponse({"detail": "unknown challenge"}, status=404)

    proof = request.GET.get("proof", "")
    if not _proof_ok(key, proof):
        return JsonResponse({"detail": "proof not accepted"}, status=403)

    return JsonResponse({"key": key, "flag": FLAGS[key]})
