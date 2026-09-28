# Review — `p1-subagents-planner-generator`

**Verdict: APPROVE**

## Summary
The unit ships exactly the three static artifacts in scope — `.claude/agents/qa-planner.md`,
`.claude/agents/qa-generator.md`, and `agent_config/product_agents.md` — plus the Tester's static
suite `agent_config/tests/test_product_agents.py`. No runtime code, no live model call, no test
generation. All 22 acceptance criteria are met and independently verified green.

## Axis 1 — Acceptance (all 22 criteria met)
- **Presence/format (1–3):** all three files present, non-empty, UTF-8.
- **Frontmatter (4–7):** both files open with a valid `---`-delimited block; `name`/`description`/
  `tools` all non-empty; `name` = `qa-planner` / `qa-generator` exactly.
- **Collision-avoidance (8–11):** neither name is in {tpm,tester,developer,reviewer,git-deployer};
  each file carries only its own `<!-- PRODUCT_AGENT: PLANNER/GENERATOR -->` marker; each
  self-identifies as a product agent; the five harness role files are unchanged (confirmed absent
  from `git diff master --name-only`).
- **References (12–14):** both files cite `agent_config/qa_system_prompt.md`, the named reliability
  rules, `Playwright MCP`, `connectors/mcp/playwright.mcp.json`, and `snapshot`.
- **Planner role (15–16):** produces a `structured test plan`; references `BRD` + the seven
  `structured` `field`s (named, not re-defined).
- **Generator role (17–18):** consumes the `plan`; authors `TypeScript`/`Playwright`/`API` tests;
  markers keep the two roles distinct.
- **Doc/determinism/placement/no-regression (19–22):** doc names both paths, both names, the
  product-vs-harness distinction, and the bound prompt; artifacts at pinned homes; suites green.

## Axis 2 — Test integrity
Tests are meaningful and un-gamed: they parse frontmatter, assert exact `name` equality, both exact
markers, cross-file distinctness (each file must NOT carry the other's marker), full set of pinned
reference substrings, and the harness-role invariant. This is the Reviewer's own run of the
Tester-authored suite; no test file was weakened. Frontmatter is parsed manually (no PyYAML dep),
matching the flat `key: value` schema — appropriate and documented in the coverage note.

## Axis 3 — Scope
No scope creep. Healer/Verifier are only mentioned in the doc as explicitly out-of-scope/later; the
glue is noted as a later unit, not implemented. No live run. `.harness/backlog.md` shows only the
orchestrator status bump (todo → spec-ready (active)); `connectors/examples/reference_app.target.json`
is a prior unit's example config, not `reference_app/**`. No protected files changed.

## Axis 4 — Quality
Correct, distinct, senior-QA-quality definitions:
- Planner tools (`Read, Grep, Glob, mcp__playwright`) are read/observe-only and it explicitly "does
  not write test code" — right for explore→plan.
- Generator tools add `Write, Edit` for authoring and it explicitly "does not plan" — right for
  plan→executable tests.
- Both defer to the QA system prompt and its named reliability rules rather than restating them;
  both ground in observed DOM snapshots via the MCP config and in the API schema.
- Collision-avoidance is genuine: distinct non-colliding names, distinct greppable markers, explicit
  product-vs-harness self-identification, and the doc deliberately placed outside `.claude/agents/`.
No dead code, no security concerns (no secrets/URLs/credentials baked in).

## Test run (independent)
```
$ uv run pytest agent_config/tests connectors/tests -q
132 passed, 1 skipped in 1.78s
```
