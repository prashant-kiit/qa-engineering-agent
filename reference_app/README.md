# Reference App

The reference app is a small, self-contained online shop (a FastAPI backend under `backend/` and a
React frontend under `frontend/`) that this project treats as a known system-under-test. It is the
app the QA agent authors and runs tests against, and the app whose bugs the evaluation harness
injects. Its intended behavior — authentication, products, cart, checkout, orders, and order-total
— is described in plain language in [`BRD.md`](./BRD.md).

For how to run and test each part, see the component docs: [`backend/README.md`](./backend/README.md)
and [`frontend/README.md`](./frontend/README.md). This top-level README documents the reference
app as a whole and the **release convention** below.

## Release convention and versioning

The reference app is versioned and "released" as a unit so that later phases can compare one
release to another. A release bundles the reference-app code together with its BRD, marks it with a
version number and a matching git tag, and enables a code-plus-BRD diff between two releases.

### Version marker

- **Location:** the canonical version lives in the plain-text file [`VERSION`](./VERSION) at the
  reference-app root (`reference_app/VERSION`).
- **Format:** a single line holding a semantic version `MAJOR.MINOR.PATCH` (each part one or more
  digits, e.g. `0.1.0`), with no prefix and no other content on the line. This is the
  machine-readable marker that tooling reads to identify the released reference-app version.
- **Current value:** `0.1.0` — the reference app's first Phase 0 release.

### Git tag scheme

Each release is marked with a git tag following the pattern **`refapp-v<MAJOR.MINOR.PATCH>`**
(for example, `refapp-v0.1.0`), where `<MAJOR.MINOR.PATCH>` equals the value in `VERSION` at
release time. Bumping the version means updating `VERSION` and creating the matching `refapp-v...`
tag. (Automating tag creation is out of scope here; this documents the agreed scheme.)

### Release bundle: code + BRD

A release of the reference app bundles the reference-app **code** (everything under
`reference_app/`) **together with** [`BRD.md`](./BRD.md). The BRD is versioned and released
alongside the code, so every release captures both the intended behavior (BRD) and the
implementation (code) at that version, identified by the version marker and the matching
`refapp-v<...>` git tag.

### How a release yields a code + BRD diff

Because each release pins both code and BRD at a known tag/version, two releases can be compared to
produce a **diff**. The code-plus-BRD diff for a release is the change **between** the previous
release's tag/version and the current one, computed over the reference-app tree (which includes
`BRD.md`). That diff is what downstream phases consume: it tells the QA agent which behavior and
which code changed from one release to the next so it can regenerate only what changed. (Computing
the diff itself is implemented in a later phase; this section defines what a release diff is.)
