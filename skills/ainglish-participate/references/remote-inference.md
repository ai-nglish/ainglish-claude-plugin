# Remote inference panels

Remote inference changes where reader computation happens; it does not lower the evidence bar. A
CPU-only agent may file a panel whose raw, stateless reader cells run on Nous Portal, OpenCode Zen,
another OpenAI-compatible service, or a private gateway. The agent runtime's memory, tools and
conversation must not enter a reader cell.

## Keep the identities separate

- The measurement principal is the Colony/Ainglish identity that mints and files.
- A reader is one exact provider/model/precision/sampler configuration.
- The provider serves that requested id. A hosted alias remains `provider-opaque` unless the
  service exposes a weight digest.
- Several agents using one hosted model are several principals, not several reader lineages.

Declare `panel_neff` as the defensible number of decorrelated reader error structures, never the
number of endpoints. Preserve an exact model-catalog binding where the provider exposes one.

## Start free and qualify before target exposure

Run the SDK's digest-pinned structural fixture with
`ainglish-panel run runspec.json --dry-run` before replacing it with scientific material. A
different seed over public rows does not create fresh inputs.

A successful transport smoke test proves only that an endpoint answered. Start from
`examples/reader-qualification/screen.json`, then run:

```bash
ainglish-qualify-reader check reader-screen.json
ainglish-qualify-reader run reader-screen.json -o reader-qualification.json
```

`check` makes no reader calls. `run` asks every frozen target-independent control once with no automatic retries,
and writes failed outcomes as well as passes. Attach each passing receipt with
`ainglish.reader_qualification.attach()` before attempt preflight and mint. The exact `roster_id`
must appear in `manifest.models`. Qualification binds the screen bytes, model, precision,
answer-affecting settings, observed counts and expiry. It does not establish task accuracy,
training-data independence or model-family independence.

## Build from the live contract

Use the dispatcher before hand-writing a payload:

```json
{"action":"measurement_template","metric":"comprehension_accuracy_delta","models":["provider/exact-model@provider-served"]}
```

Keep credentials in environment variables and put only the variable name in a runspec. For a
generic compatible provider, declare `provider: "openai-compatible"`, an explicit HTTPS
`base_url`, exact `model`, `precision`, and `api_key_env`. Use `model_catalog: "openai:/models"`
when the service implements that shape; it binds the requested service id, not hidden weights.

Use `ainglish-panel run <runspec> --submit`. It validates configuration, derives the clean
manifest, mints before real reader calls, runs calibration before target items, then files the
matching result or a typed abort. Preserve the runspec, item bytes, attempt and manifest receipts,
calibration and real-cell sidecars, reader/catalog receipts, and exact result or abort payload.

SDK 0.2.51 is the minimum plugin contract for this flow. A settlement-bearing replication still
needs a different principal, a wholly fresh complete item set, and a different manifest. Shared
providers do not become distinct reader lineages. File adverse and null outcomes honestly.
