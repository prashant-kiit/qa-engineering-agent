# Review — p0-brd-release

**Verdict: APPROVE**

## Axis findings

### 1. Acceptance (criteria 1–20) — all met
- **BRD (`reference_app/BRD.md`)** — freeform prose, zero code fences. Covers all six required
  flows: authentication (sign-in w/ credentials, invalid/missing rejected as unauthorized),
  products (catalog with name + price), cart/add-to-cart (explicitly cumulative quantity, w/ a
  2+3=5 worked example), checkout (empty-cart rejected, non-empty creates order + clears cart),
  orders (retrievable, reflects purchased items), order-total (per-line price × quantity, summed;
  order total == cart total at checkout). C1–C9 pass.
- **Release README (`reference_app/README.md`)** — has a "Release convention and versioning"
  heading; names the marker location (`reference_app/VERSION`) + semver format; documents the
  `refapp-v<MAJOR.MINOR.PATCH>` tag scheme; explains the code+BRD diff as the change *between* two
  releases' tags/versions over the reference-app tree; references `BRD.md` as bundled alongside
  code. C10–C15 pass.
- **Version marker (`reference_app/VERSION`)** — single semver line `0.1.0`; README documents the
  same value. C16–C18 pass.
- **No regressions** — sub-READMEs and protected docs/source unchanged. C19–C20 pass.

### 2. Test integrity — sound, un-gamed
- Tests match the Tester's coverage-note mapping 1:1 and were not modified by the developer
  (the three source files are the only developer-added artifacts).
- C2 (zero triple-backtick fences) is a real freeform-prose guard, not trivially satisfiable.
- C19/C20 regression guards use `shasum -a 256 -c` against recorded baselines — genuine content
  hashes, meaningful. Verified they stay green with the three new additive files present; they
  would flip red on any touch to a sub-README, protected doc, or backend/frontend source. The
  C20 baseline for `AGILE_PLAN.md` matches the current file (the plan-lock edit predates the
  Tester's baseline snapshot), so the guard correctly reports no source/protected change from
  this unit.

### 3. Scope — clean
Developer added exactly `reference_app/BRD.md`, `reference_app/README.md`, `reference_app/VERSION`.
No backend/frontend/source edits; existing `backend/README.md` and `frontend/README.md` untouched
(C19). The modified `AGILE_PLAN.md` / `.harness/backlog.md` are harness/TPM process artifacts, not
developer source changes, and C20 confirms `AGILE_PLAN.md` content is unchanged vs baseline.

### 4. Quality — BRD is truthful vs the shipped backend contract
Cross-checked `reference_app/backend/app.py`:
- Cumulative add: `UPDATE cart_items SET quantity = quantity + ?` — matches BRD.
- Empty-cart checkout → HTTP 400 "Cannot checkout an empty cart" — matches "not allowed".
- Unknown product → HTTP 404 — matches "refused, cart unchanged".
- Order retrieval → 404 if absent; reflects order_items — matches BRD.
- Total = `price * quantity` summed over lines; order.total set from cart lines at checkout —
  matches "order total equals cart total at checkout".
- Basic-auth, 401 on invalid/missing credentials — matches BRD.
No described behavior contradicts the contract or claims features the app lacks. README release
convention is internally coherent and consistent with `DESIGN.md §7/§8/§9`.

## Test runs (all green)

```
bash tests/docs/brd-release.test.sh          -> RESULT: all acceptance checks passed (exit 0; 20/20)
uv run pytest reference_app/backend/tests -q -> 26 passed, 1 warning
npm --prefix reference_app/frontend test     -> Test Files 6 passed (6); Tests 17 passed (17)
bash tests/scaffold/p0-scaffold.test.sh      -> RESULT: all acceptance checks passed (exit 0)
bash tests/docs/design-note.test.sh          -> RESULT: all acceptance checks passed (exit 0)
```
