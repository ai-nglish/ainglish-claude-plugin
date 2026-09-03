"""Offline checks for the canonical language-reference sync contract."""

import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("sync_reference", ROOT / "tools" / "sync_reference.py")
sync_reference = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_reference)


def fixture():
    canonical = b'{"count":0,"entries":[],"kind":"ainglish.register"}'
    digest = hashlib.sha256(canonical).hexdigest()
    reference = (
        "# The Ainglish register — agent reference\n\n"
        "> Format: `ainglish.agent-reference.v1`\n"
        "> Register version: `0.35.0`\n"
        f"> Register SHA-256: `{digest}`\n"
        "> Source bytes: `GET /api/v1/register.canonical`\n"
    ).encode()
    return reference, canonical, digest


def test_reference_is_bound_to_independently_fetched_register_bytes():
    reference, canonical, digest = fixture()
    receipt = sync_reference.validate(
        reference, canonical,
        {"x-register-digest": digest, "x-ainglish-reference-format": sync_reference.FORMAT},
        {"x-register-digest": digest},
    )
    assert receipt["register_digest"] == digest
    assert receipt["version"] == "0.35.0"


def test_reference_refuses_a_digest_claim_for_different_bytes():
    reference, canonical, _ = fixture()
    try:
        sync_reference.validate(reference, canonical + b"\n", {}, {})
    except ValueError as error:
        assert "does not match" in str(error)
    else:
        raise AssertionError("digest mismatch was accepted")


def test_reference_refuses_unknown_compiler_format():
    reference, canonical, _ = fixture()
    reference = reference.replace(b"ainglish.agent-reference.v1", b"ainglish.agent-reference.v9")
    try:
        sync_reference.validate(reference, canonical, {}, {})
    except ValueError as error:
        assert "unsupported" in str(error)
    else:
        raise AssertionError("unknown format was accepted")


def test_remote_inference_guidance_is_linked_and_pins_current_contract():
    skill = (ROOT / "skills" / "ainglish-participate" / "SKILL.md").read_text(encoding="utf-8")
    reference = ROOT / "skills" / "ainglish-participate" / "references" / "remote-inference.md"

    assert "references/remote-inference.md" in skill
    text = reference.read_text(encoding="utf-8")
    for contract in (
        "0.2.51", "preflight", "reader_qualification.attach", "panel_neff",
        "wholly fresh", "no automatic retries",
    ):
        assert contract in text
