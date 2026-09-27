# Task: p0-brd-release

## Title
Reference shop **BRD** (freeform intended behavior) + a documented **release convention** (version
marker + tag scheme + how a release yields a code+BRD diff)

## Context
- Plan item: `AGILE_PLAN.md` → Phase 0, **B3. BRD + release convention**; backlog unit
  **#4 (`p0-brd-release`)**.
- Depends on: **`p0-shop-backend`** (done). The clean shop backend
  (`reference_app/backend/app.py`, contract in `.harness/tasks/p0-shop-backend.md`) and the shop
  frontend (`reference_app/frontend/`, contract in `reference_app/frontend/README.md`) already exist
  and define the actual behavior the BRD must describe in prose.
- Source of truth: `DESIGN.md §8` (versioning & hashing — BRD is **freeform/content-hashed**, a
  release diffs hashes to regenerate only what changed), `DESIGN.md §9` (reference app = shop we
  "release"), `DESIGN.md §7` (Case 1 release-triggered = BRD + code diff from that release), and
  `AGILE_PLAN.md` B3.
- **Why this unit exists / who consumes it:** the `BRD.md` is the human-readable *intended behavior*
  that **Phase 1 Case 1** (auto-synthesized test fields from BRD + code) and **Phase 4**
  change-detection will diff against. The **release convention** is the agreed way a "release" of the
  reference app bundles code + BRD so a later phase can compute a code+BRD diff between two releases.
- This is a **documentation + convention + a version marker** unit. It does **not** build any diff,
  hashing, tagging automation, or change-detection tooling — that is Phase 4.

## Scope
**In scope**
1. Author `reference_app/BRD.md` — a **freeform, prose** business-requirements description of the
   shop's intended behavior, covering (at minimum) the flows: **authentication**, **products**,
   **cart / add-to-cart**, **checkout**, **orders**, and **order-total**. Prose only (no code, no
   OpenAPI dump, no test steps) — it reads as intended behavior a human QA lead would write.
2. Author `reference_app/README.md` — documents (a) what the reference app is, and (b) the
   **release convention**: the version marker (its exact location + format), the git **tag scheme**,
   and **how a release yields a code+BRD diff** between two releases (which artifacts are included in
   a release bundle, and how two releases are compared).
3. Introduce a concrete, machine-readable **version marker** at the pinned location + format defined
   in Interfaces below, so a presence/structure test can assert it exists and is well-formed.

**Out of scope**
- Any **diff, content-hashing, or change-detection code/tooling** — that is Phase 4
  (`META_PLAN.md` Phase 4). This unit only *documents the convention* and *pins the marker*.
- Any **tagging automation / release script / CI workflow** — describe the tag scheme in prose only.
- Editing the backend or frontend behavior, adding endpoints, or changing seed data.
- The Playwright project / `eval/` harness (units 5, 6).
- Editing `DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, or anything under `.harness/`.
- Editing the existing `reference_app/backend/README.md` or `reference_app/frontend/README.md`
  (this unit adds a *new* top-level `reference_app/README.md`; the sub-READMEs stay as-is).

## Acceptance criteria (enumerated, testable — presence / structure checks)
These are verifiable by presence + structure/grep checks against the files, without executing code.

**BRD — `reference_app/BRD.md`**
1. The file `reference_app/BRD.md` **exists** and is non-empty.
2. It is **prose / freeform** (Markdown narrative), not code or a spec dump: it contains no fenced
   code blocks presenting source/OpenAPI/test code, and reads as human-authored requirements.
3. It describes the **authentication** flow (a user must sign in with credentials to use the shop;
   valid credentials grant access, invalid/missing credentials are rejected).
4. It describes **products** (the shop presents a catalog of products the user can browse, each with
   at least a name and a price).
5. It describes the **cart / add-to-cart** behavior (a user adds products to a cart; adding the same
   product again increases its quantity cumulatively rather than resetting it).
6. It describes **checkout** (a user with a non-empty cart can check out, which creates an order;
   checking out an empty cart is not allowed).
7. It describes **orders** (an order created at checkout can be retrieved afterward, and reflects the
   items that were purchased).
8. It describes the **order-total** rule in intent terms (the total is the sum, over each line, of
   the product's price times its quantity; the order's total equals the cart total at checkout).
9. The described behavior is **consistent** with the shipped app (no flow contradicts
   `.harness/tasks/p0-shop-backend.md` / the backend contract) — e.g. it does not describe features
   the app lacks or contradict the cumulative-add or empty-cart-rejection rules.

**Release README — `reference_app/README.md`**
10. The file `reference_app/README.md` **exists** and is non-empty.
11. It documents the **release convention** with a clearly identifiable section (heading) about
    **releases / versioning**.
12. It names the **version marker** — its **exact location** and **format** (matching the pinned
    contract in Interfaces below) — so a reader knows where the version lives and how to read it.
13. It documents a **git tag scheme** for releases (the exact tag-name pattern used to mark a
    release, per Interfaces below).
14. It explains **how a release yields a code+BRD diff**: that a release bundles the reference app
    **code together with `BRD.md`**, and that two releases are compared (e.g. between their tags /
    version markers) to produce the diff consumed by Phase 1 Case 1 / Phase 4 change-detection.
15. It references `BRD.md` as part of the release bundle (BRD is versioned/released alongside code).

**Version marker (pinned location + format)**
16. The **version marker** exists at the pinned path `reference_app/VERSION` (see Interfaces).
17. Its content is a **single semantic-version line** matching `MAJOR.MINOR.PATCH` (digits and dots
    only, e.g. `0.1.0`), with no other content required on that line.
18. The version value documented in `reference_app/README.md` (criterion 12) is **consistent** with
    the value actually present in `reference_app/VERSION` (same version string).

**No regressions**
19. The pre-existing `reference_app/backend/README.md` and `reference_app/frontend/README.md` are
    **unchanged** by this unit (the new docs are additive at `reference_app/` top level).
20. No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`,
    `.harness/**`), and no backend/frontend source is modified.

## Interfaces / contracts
> Paths, the version-marker location/format, and the required doc topics below are **binding** so a
> presence/structure test can assert them without reading prose intent.

### Files (exact paths)
- `reference_app/BRD.md` — freeform BRD (new).
- `reference_app/README.md` — reference-app overview + release convention (new, top-level of
  `reference_app/`; distinct from the existing `backend/README.md` and `frontend/README.md`).
- `reference_app/VERSION` — the canonical version marker (new).

### Version marker (binding location + format)
- **Location:** `reference_app/VERSION` (a plain-text file at the reference-app root).
- **Format:** a **single line** containing a semantic version `MAJOR.MINOR.PATCH` (each part is one
  or more digits), e.g. `0.1.0`. No prefix, no trailing commentary on that line. A trailing newline
  is allowed. This is the machine-readable marker a presence test asserts and that future tooling
  (Phase 4) reads to identify the released reference-app version.
- **Initial value:** `0.1.0` (the reference app's first Phase 0 release).

### Git tag scheme (documented in prose, not automated here)
- Release tags follow the pattern **`refapp-v<MAJOR.MINOR.PATCH>`** (e.g. `refapp-v0.1.0`), where the
  `<MAJOR.MINOR.PATCH>` equals the value in `reference_app/VERSION` at release time. `reference_app/README.md`
  must document this pattern. (Actually creating tags / a tagging script is out of scope.)

### Release bundle & diff (documented in prose, not automated here)
- A "release" of the reference app bundles the **reference-app code** (under `reference_app/`)
  **together with `reference_app/BRD.md`**, identified by the version marker + matching git tag.
- The **code+BRD diff** for a release is the change between the previous release's tag/version and
  the current one, over the reference-app tree (which includes `BRD.md`). `reference_app/README.md`
  must describe this comparison in prose so Phase 1 Case 1 / Phase 4 know what a release diff is.
  Implementing the diff computation is **explicitly Phase 4**, out of scope for this unit.

### Required topic coverage (for the Tester's structure checks)
- `BRD.md` must contain identifiable prose coverage of each of: **auth, products, cart/add-to-cart,
  checkout, orders, order-total** (criteria 3–8).
- `README.md` must contain identifiable sections/statements for: **version marker location+format,
  git tag scheme, release bundle = code + BRD, and how two releases yield a diff** (criteria 11–15).

## Definition of Done
- All acceptance criteria **1–20** are satisfied by presence/structure checks.
- `reference_app/BRD.md`, `reference_app/README.md`, and `reference_app/VERSION` exist with the
  pinned paths, formats, and topic coverage above; the version value is consistent across the marker
  and the README.
- The BRD is freeform prose consistent with the shipped shop behavior; the release convention is
  fully *documented* (version marker + tag scheme + code+BRD diff) with **no** diff/hashing/tagging
  code built (that is Phase 4).
- Existing backend/frontend READMEs and all protected files are unchanged.
- Consistent with `DESIGN.md §7/§8/§9` and `AGILE_PLAN.md` B3; supports Phase 0 acceptance
  ("`BRD.md` exists") and unblocks Phase 1 Case 1 / Phase 4 change-detection.
