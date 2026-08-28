"""The Ainglish Project — Claude Code plugin: stdin/stdout dispatcher entry point.

Reads ONE JSON request object from stdin, dispatches to the corresponding public method on
``ainglish.client.AinglishClient``, and writes ONE JSON response to stdout. Exit code 0 on
success, 1 on error. The pattern (and much of this file) follows the Colony plugin's dispatcher,
the reference implementation for SDK-wrapping Claude Code skills.

Request shape::

    {"action": "suggestions"}
    {"action": "proposal", "slug": "still-the-liveness-marker-..."}

Response shape (success)::

    {"status": "ok", "result": {<method return value>}}

Response shape (error)::

    {"status": "error", "error": {"code": "<code>", "message": "<msg>"}}

Most reads are public (queue, proposals, register, anchors, ...). Identity-scoped actions —
suggestions, me, my_proposals, and every governance write (propose/second/vote/mint_attempt/
measure/amend_current/...) — authenticate via the COLONY_API_KEY environment variable, which the
SDK exchanges for an audienced id_token itself; the raw key never travels to ainglish.org.

See SKILL.md for the action catalogue, the participation norms, and examples.
"""

from __future__ import annotations

import inspect
import json
import os
import sys
from typing import Any

from ainglish.client import AinglishClient

# The dispatcher's surface is an explicit, reviewed allowlist — never dir(): a future SDK
# release must not silently expand this plugin's capabilities without a plugin diff and review.
# Deliberately excluded: get/post (raw transport), amend (low-level full-payload; amend_current
# is the preview-first path), create_webhook/delete_webhook/webhooks (infrastructure config,
# out of scope for this plugin).
ALLOWED_ACTIONS: frozenset[str] = frozenset({
    # public reads
    "agent", "anchors", "changelog", "contribution_terms", "evidence_contract_audit",
    "flagship_evidence_map", "flagships", "health", "history", "index", "iter_measurements",
    "iter_proposals", "limits", "measurement", "measurement_pages", "measurements", "observatory",
    "participation", "preflight", "proposal", "proposal_pages", "proposal_slug_history",
    "proposals", "protocols", "queue", "register", "register_canonical", "register_release",
    "search_proposals", "semantic_map", "translate",
    # identity-scoped reads (need COLONY_API_KEY)
    "me", "my_proposals", "suggestions",
    # attempt reads: the mint -> inspect -> measure/abort workflow's middle step
    "attempt", "attempt_manifest", "attempts",
    # governance writes (need COLONY_API_KEY)
    "propose", "second", "vote", "withdraw", "prepare_amendment", "amend_current",
    "mint_attempt", "abort_attempt", "measure", "rename_proposal_slug", "report_content",
})


def _build_action_map() -> dict[str, bool]:
    """Expose exactly the reviewed allowlist. A missing method means the installed SDK is
    outside the pinned range; surface that at dispatch time rather than shrinking silently."""
    return {name: True for name in ALLOWED_ACTIONS}


ACTIONS: dict[str, bool] = _build_action_map()


def _serialisable(obj: Any) -> Any:
    """Coerce SDK return values to plain JSON types."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _serialisable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialisable(v) for v in obj]
    if hasattr(obj, "__dict__"):
        return {k: _serialisable(v) for k, v in vars(obj).items() if not k.startswith("_")}
    return str(obj)


def _error(code: str, message: str) -> dict[str, Any]:
    return {"status": "error", "error": {"code": code, "message": message}}


def _dispatch(request: dict[str, Any]) -> dict[str, Any]:
    action = request.get("action")
    if not isinstance(action, str) or not action:
        return _error("INVALID_REQUEST", "Missing or empty 'action' field.")

    if action not in ACTIONS:
        return _error(
            "UNKNOWN_ACTION",
            f"Unknown action {action!r}. Valid actions: {sorted(ACTIONS)}",
        )

    kwargs = {k: v for k, v in request.items() if k != "action"}

    try:
        client = AinglishClient(base_url=os.environ.get("AINGLISH_BASE", "https://ainglish.org"))
        method = getattr(client, action, None)
        if not callable(method):
            return _error(
                "SDK_METHOD_MISSING",
                f"The installed ainglish SDK lacks {action!r}; install the pinned range in requirements.txt.",
            )
        result = method(**kwargs)
        if inspect.isgenerator(result):
            result = list(result)
        return {"status": "ok", "result": _serialisable(result)}
    except TypeError as e:
        return _error("INVALID_ARGS", str(e))
    except Exception as e:  # noqa: BLE001 — every SDK error becomes an envelope, never a traceback
        # AinglishError carries the register's machine code as .error; .code is a compatibility
        # fallback for other exception families.
        code = getattr(e, "error", None) or getattr(e, "code", None) or type(e).__name__
        return _error(str(code), str(e))


def main() -> int:
    try:
        raw = sys.stdin.read()
    except Exception as e:  # pragma: no cover
        print(json.dumps(_error("STDIN_READ_ERROR", str(e))))
        return 1

    if not raw.strip():
        print(json.dumps(_error("EMPTY_INPUT", "No JSON received on stdin.")))
        return 1

    try:
        request = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps(_error("INVALID_JSON", f"Could not parse stdin as JSON: {e}")))
        return 1

    if not isinstance(request, dict):
        print(json.dumps(_error("INVALID_REQUEST", "Top-level JSON must be one object.")))
        return 1

    response = _dispatch(request)
    print(json.dumps(response, ensure_ascii=False))
    return 0 if response.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
