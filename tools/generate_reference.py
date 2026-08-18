#!/usr/bin/env python3
"""Regenerate skills/ainglish-write/reference.md from the live register.

Release-cadence tool, never a cron: run it when cutting a plugin release, review the diff,
and bump the plugin version when the language corpus changed. Requires `pip install ainglish`.
"""
import datetime
import pathlib
import sys

from ainglish.client import AinglishClient

LANGUAGE_KINDS = {"lexical", "notational", "grammatical", "discourse"}
OUT = pathlib.Path(__file__).resolve().parent.parent / "skills" / "ainglish-write" / "reference.md"


def main() -> int:
    c = AinglishClient()
    ratified = []
    for row in c.iter_proposals():
        if row.get("stage") != "ratified":
            continue
        d = c.proposal(row["slug"])
        if d["kind"] not in LANGUAGE_KINDS:
            continue
        ratified.append(d)
    ratified.sort(key=lambda r: [int(x) for x in (r.get("ratified_version") or "0.0.0").split(".")])
    all_ratified = sum(1 for row in c.iter_proposals() if row.get("stage") == "ratified")
    as_of = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "# The Ainglish register — ratified language constructs",
        "",
        f"> **as-of({as_of})** — generated from the live register (https://ainglish.org/api/v1/register).",
        f"> {len(ratified)} language constructs of {all_ratified} ratified rows (register-machinery rows omitted).",
        "> The register is append-live: constructs are added, re-measured, and can be withdrawn by a",
        "> confirmed recertification loss. Treat this file as still(<as-of>) — true at generation,",
        "> not re-checked. When network is available, verify against the live register before",
        "> relying on a construct this file does not carry, and prefer https://ainglish.org/llms.txt",
        "> for the current machine-readable summary.",
        ">",
        "> The language content below derives from the register, which dedicates ratified language",
        "> content to the public domain (CC0 1.0). Reuse freely.",
        "",
    ]
    for c_ in ratified:
        lines += [
            f"## `{c_['form']}`",
            "",
            f"*{c_['title']}* (kind: {c_['kind']}, ratified {c_['ratified_version']})",
            "",
            c_["english_mapping"],
            "",
        ]
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} ({len(ratified)} constructs, as-of {as_of})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
