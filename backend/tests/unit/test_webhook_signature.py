"""Unit tests for webhook signature verification — T-101."""

import hashlib
import hmac
import pytest
from app.api.routes.webhooks import verify_github_webhook_signature


SECRET = "test-webhook-secret-abc123"


def make_signature(payload: bytes, secret: str) -> str:
    """Helper: generate a valid HMAC-SHA256 signature."""
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_valid_signature_passes() -> None:
    """T-101: Valid HMAC signature should return True."""
    payload = b'{"action": "opened", "pull_request": {}}'
    sig = make_signature(payload, SECRET)
    assert verify_github_webhook_signature(payload, sig, SECRET) is True


def test_tampered_payload_fails() -> None:
    """T-101: Tampered payload with unchanged signature should return False."""
    original = b'{"action": "opened"}'
    tampered = b'{"action": "synchronize"}'
    sig = make_signature(original, SECRET)
    assert verify_github_webhook_signature(tampered, sig, SECRET) is False


def test_missing_signature_header_fails() -> None:
    """T-101: Missing signature header should return False."""
    payload = b'{"action": "opened"}'
    assert verify_github_webhook_signature(payload, None, SECRET) is False


def test_wrong_prefix_fails() -> None:
    """T-101: Signature without 'sha256=' prefix should return False."""
    payload = b'{"action": "opened"}'
    sig = make_signature(payload, SECRET)
    bad_sig = sig.replace("sha256=", "sha1=")
    assert verify_github_webhook_signature(payload, bad_sig, SECRET) is False


def test_wrong_secret_fails() -> None:
    """T-101: Signature made with a different secret should return False."""
    payload = b'{"action": "opened"}'
    sig = make_signature(payload, "different-secret")
    assert verify_github_webhook_signature(payload, sig, SECRET) is False


def test_empty_signature_fails() -> None:
    """T-101: Empty string signature should return False."""
    payload = b'{"action": "opened"}'
    assert verify_github_webhook_signature(payload, "", SECRET) is False
