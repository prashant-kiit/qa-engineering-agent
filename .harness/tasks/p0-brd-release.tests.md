# Test coverage — `p0-brd-release`

TDD **red** phase. Tests were written from `.harness/tasks/p0-brd-release.md` before any
implementation exists. All checks are automated presence/structure/grep assertions (no code
executed), following the existing bash pattern in `tests/docs/design-note.test.sh`.

## Test files created
- `tests/docs/brd-release.test.sh` — the suite (runnable: `bash tests/docs/brd-release.test.sh`;
  exit 0 = all pass, 1 = any fail, 2 = scaffolding error).
- `tests/fixtures/p0-brd-release-readme-baseline.sha256` — sha256 baseline of the two pre-existing
  sub-READMEs (backend/frontend) for the no-regression check (C19).
- `tests/fixtures/p0-brd-release-protected-baseline.sha256` — sha256 baseline of protected docs
  (DESIGN/META_PLAN/AGILE_PLAN/CLAUDE) + backend/frontend **source** files (C20). Excludes the
  mutable `shop.db`, `dist/` build output, and lockfiles to avoid flaky failures.

## Acceptance criterion → test mapping
| # | Criterion (spec) | Test check |
|---|---|---|
| 1 | `reference_app/BRD.md` exists & non-empty | C1 |
| 2 | BRD is prose/freeform (no fenced code blocks) | C2 (asserts zero ` ``` ` fence lines) |
| 3 | BRD describes authentication (credentials; invalid rejected) | C3 |
| 4 | BRD describes products (catalog, name, price) | C4 |
| 5 | BRD describes cart / add-to-cart (cumulative quantity) | C5 |
| 6 | BRD describes checkout (empty cart not allowed → order) | C6 |
| 7 | BRD describes orders (retrievable, reflects purchased items) | C7 |
| 8 | BRD describes order-total (sum of price × quantity) | C8 |
| 9 | BRD consistent w/ backend (cumulative-add + empty-cart-reject invariants) | C9 |
| 10 | `reference_app/README.md` exists & non-empty | C10 |
| 11 | README has a release/versioning section heading | C11 |
| 12 | README names version-marker location (`VERSION`) + format (semver) | C12 |
| 13 | README documents git tag scheme `refapp-v<MAJOR.MINOR.PATCH>` | C13 |
| 14 | README explains how two releases yield a code+BRD diff | C14 |
| 15 | README references `BRD.md` as part of the release bundle | C15 |
| 16 | `reference_app/VERSION` exists at pinned path | C16 |
| 17 | VERSION is a single semver line `MAJOR.MINOR.PATCH` | C17 (regex `^[0-9]+\.[0-9]+\.[0-9]+$`, exactly one non-empty line) |
| 18 | README version value consistent with VERSION value | C18 (extracts VERSION string, greps README) |
| 19 | Pre-existing backend/frontend READMEs unchanged | C19 (sha256 vs baseline) |
| 20 | No protected file / backend/frontend source modified | C20 (sha256 vs baseline) |

## Soundness verification
The script was validated against a temporary correct fixture (BRD.md + README.md + VERSION with
`0.1.0`): **all 20 checks passed (exit 0)**. The fixture files were then removed, restoring red.
This confirms the failures below are legitimate missing-behavior failures, not harness/syntax errors.

## Red run output
`bash tests/docs/brd-release.test.sh` (exit code 1):

```
FAIL: C1: reference_app/BRD.md exists and is non-empty
FAIL: C2: BRD is prose/freeform (no fenced code blocks) -- file missing
FAIL: C3: BRD describes authentication (sign-in w/ credentials, invalid rejected)
FAIL: C4: BRD describes products (catalog with name & price)
FAIL: C5: BRD describes cart / add-to-cart with cumulative quantity
FAIL: C6: BRD describes checkout (empty cart not allowed -> creates order)
FAIL: C7: BRD describes orders (retrievable, reflects purchased items)
FAIL: C8: BRD describes order-total rule (sum of price * quantity)
FAIL: C9: BRD is consistent w/ backend (cumulative-add & empty-cart-rejection invariants present)
FAIL: C10: reference_app/README.md exists and is non-empty
FAIL: C11: README has a release/versioning section heading
FAIL: C12: README names the version marker location (VERSION) + format (semver)
FAIL: C13: README documents the git tag scheme 'refapp-v<...>'
FAIL: C14: README explains how two releases yield a code+BRD diff
FAIL: C15: README references BRD.md as part of the release bundle (code + BRD)
FAIL: C16: reference_app/VERSION exists at the pinned path
FAIL: C17: VERSION is a single semver line -- file missing
FAIL: C18: cannot verify README/VERSION consistency (VERSION not a valid semver)
PASS: C19: backend/README.md & frontend/README.md unchanged (additive docs)
PASS: C20: protected docs & backend/frontend source unchanged
-----------------------------------------------------------------------
RESULT: 18 acceptance check(s) failed
```

**Note on C19/C20:** these two pass *now* because nothing has been modified yet — they are
regression guards that must **stay** green after the Developer adds the three new files. They
correctly turn red if the Developer touches a sub-README, a protected doc, or backend/frontend
source. Criteria 1–18 (all target-file behavior) are legitimately red pending implementation.
