"""Dispatcher unit tests — offline: the client is monkeypatched, no network is touched."""

import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "participate_main",
    Path(__file__).resolve().parent.parent / "skills" / "ainglish-participate" / "main.py",
)
main = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(main)


def run(request, monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(request) if isinstance(request, dict) else request))
    code = main.main()
    out = capsys.readouterr().out.strip()
    return code, json.loads(out)


def test_action_surface_is_exactly_the_reviewed_allowlist():
    # Both directions pinned: nothing silently added by a future SDK, nothing silently dropped.
    assert set(main.ACTIONS) == set(main.ALLOWED_ACTIONS)
    for excluded in ("get", "post", "amend", "webhooks", "create_webhook", "delete_webhook"):
        assert excluded not in main.ACTIONS
    # every allowed action exists on the pinned SDK, so SDK_METHOD_MISSING cannot fire in-range
    from ainglish.client import AinglishClient
    import inspect as _inspect
    for name in main.ALLOWED_ACTIONS:
        assert callable(_inspect.getattr_static(AinglishClient, name)), name


def test_unknown_action_is_a_typed_error(monkeypatch, capsys):
    code, resp = run({"action": "definitely_not_a_method"}, monkeypatch, capsys)
    assert code == 1
    assert resp["status"] == "error"
    assert resp["error"]["code"] == "UNKNOWN_ACTION"
    # the error names the valid actions so the caller can self-correct
    assert "proposal" in resp["error"]["message"]


def test_invalid_json_is_a_typed_error(monkeypatch, capsys):
    code, resp = run("{not json", monkeypatch, capsys)
    assert code == 1
    assert resp["error"]["code"] == "INVALID_JSON"


def test_empty_input_is_a_typed_error(monkeypatch, capsys):
    code, resp = run("", monkeypatch, capsys)
    assert code == 1
    assert resp["error"]["code"] == "EMPTY_INPUT"


def test_dispatch_calls_the_named_method_with_kwargs(monkeypatch, capsys):
    calls = {}

    class FakeClient:
        def __init__(self, base_url="https://ainglish.org"):
            calls["base_url"] = base_url

        def proposal(self, slug):
            calls["slug"] = slug
            return {"slug": slug, "stage": "proposed"}

    monkeypatch.setattr(main, "AinglishClient", FakeClient)
    code, resp = run({"action": "proposal", "slug": "some-row"}, monkeypatch, capsys)
    assert code == 0
    assert resp == {"status": "ok", "result": {"slug": "some-row", "stage": "proposed"}}
    assert calls == {"base_url": "https://ainglish.org", "slug": "some-row"}


def test_wrong_kwargs_surface_as_invalid_args(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, base_url=""):
            pass

        def proposal(self, slug):  # noqa: ARG002
            return {}

    monkeypatch.setattr(main, "AinglishClient", FakeClient)
    code, resp = run({"action": "proposal", "nope": "x"}, monkeypatch, capsys)
    assert code == 1
    assert resp["error"]["code"] == "INVALID_ARGS"


def test_real_ainglish_errors_keep_their_machine_code(monkeypatch, capsys):
    # The SDK's typed error carries the register's machine code as .error — the dispatcher must
    # surface THAT, not the exception class name (Dexagon's #1 review, blocking item 3).
    from ainglish.client import AinglishError

    class FakeClient:
        def __init__(self, base_url=""):
            pass

        def second(self, slug):
            raise AinglishError(422, {"error": "rejected", "message": "This proposal cannot accept a second."})

    monkeypatch.setattr(main, "AinglishClient", FakeClient)
    code, resp = run({"action": "second", "slug": "row"}, monkeypatch, capsys)
    assert code == 1
    assert resp["error"]["code"] == "rejected"
    assert "cannot accept a second" in resp["error"]["message"]


def test_code_attribute_remains_a_compatibility_fallback(monkeypatch, capsys):
    class Boom(Exception):
        code = "rate_limited"

    class FakeClient:
        def __init__(self, base_url=""):
            pass

        def second(self, slug):
            raise Boom("slow down")

    monkeypatch.setattr(main, "AinglishClient", FakeClient)
    code, resp = run({"action": "second", "slug": "row"}, monkeypatch, capsys)
    assert code == 1
    assert resp["error"] == {"code": "rate_limited", "message": "slow down"}
