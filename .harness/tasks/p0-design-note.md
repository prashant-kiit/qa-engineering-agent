# Task: p0-design-note

## Title
Record explicit post-v1 scope in `DESIGN.md §15`

## Context
- Plan item: `AGILE_PLAN.md` → "Task 0 (do first): record post-v1 scope in `DESIGN.md §15`".
- Backlog unit #0 (`p0-design-note`), no dependencies.
- Doc-only unit. `META_PLAN.md` "Post-v1" section already names two items as out of the first
  release; `DESIGN.md §15` currently lists them among "open / deferred items" but does **not**
  explicitly mark them as post-v1 / not in the first SaaS release. This unit adds that explicit
  marker so §15 is unambiguous about what ships in v1 vs. what is deferred.

## Scope
**In scope**
- Add one explicit "post-v1" note to `DESIGN.md`, Section 15 ("Open / deferred items"), stating that
  the two named items are out of the first SaaS release and that all other §15 items are
  implemented in-phase (only their fine detail / eval-driven choice deferred).
- The two named post-v1 items:
  - (a) target-app auth beyond Basic Auth — SSO/MFA;
  - (b) data residency & retention policy per tenant tier.

**Out of scope**
- Any code, tests, or build tooling.
- Editing any file other than `DESIGN.md`.
- Restructuring, renumbering, or deleting existing §15 bullets or any other section.
- Changing `META_PLAN.md` or `AGILE_PLAN.md`.

## Acceptance criteria (testable via presence checks)
1. `DESIGN.md` contains Section 15 titled "Open / deferred items" (the heading `## 15. Open /
   deferred items` still exists and is unchanged).
2. Within Section 15, a distinct note is present that explicitly designates scope as post-v1 —
   i.e. the note contains the phrase indicating "post-v1" **and** the phrase indicating it is not in
   the first SaaS release (e.g. "not in first SaaS release").
3. That note references item (a): target-app auth beyond Basic Auth, naming **SSO/MFA**.
4. That note references item (b): **data residency & retention policy per tenant tier**.
5. That note states that all other §15 items are implemented in-phase and only their fine detail /
   eval-driven choice is deferred.
6. No pre-existing §15 bullet is removed; the note is additive (existing bullets remain present).
7. `DESIGN.md` remains a well-formed Markdown document (no broken/duplicated section headings).

Reference wording (may be used verbatim; equivalent phrasing that satisfies criteria 2–5 is also
acceptable):
> **Explicitly post-v1 (not in first SaaS release):** (a) target-app auth beyond Basic Auth —
> SSO/MFA; (b) data residency & retention policy per tenant tier. All other §15 items are
> implemented in-phase; only their fine detail / eval-driven choice is deferred.

## Interfaces / contracts
- File: `/Users/prashant/Desktop/Project/qa-engineering-agent/DESIGN.md`.
- Location: Section `## 15. Open / deferred items`.
- No public API, no code interface.

## Definition of Done
- All acceptance criteria 1–7 verified by a presence/grep check against `DESIGN.md`.
- No file other than `DESIGN.md` changed.
- Change is reviewable as a small, additive documentation diff consistent with `META_PLAN.md`
  "Post-v1" scope.
