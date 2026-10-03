# Test coverage — `p1-subagents-planner-generator` (TDD red)

**Test file (new):** `agent_config/tests/test_product_agents.py`
**Run:** `uv run pytest agent_config/tests -q` (or the file directly)
**Under test (not created by the Tester):** `.claude/agents/qa-planner.md`,
`.claude/agents/qa-generator.md`, `agent_config/product_agents.md`.

All tests are purely static: they read/parse committed text only. No model call,
agent run, MCP start, browser launch, or network I/O.

## Acceptance criterion → test mapping

| # | Criterion | Test(s) |
|---|---|---|
| 1 | Planner file present, non-empty, UTF-8 | `test_c1_planner_file_present_nonempty_utf8` |
| 2 | Generator file present, non-empty, UTF-8 | `test_c2_generator_file_present_nonempty_utf8` |
| 3 | Doc present, non-empty | `test_c3_doc_present_nonempty` |
| 4 | Planner valid frontmatter (name/description/tools non-empty) | `test_c4_planner_valid_frontmatter_required_fields` |
| 5 | Generator valid frontmatter (name/description/tools non-empty) | `test_c5_generator_valid_frontmatter_required_fields` |
| 6 | Planner `name` == `qa-planner` | `test_c6_planner_name_is_pinned_value` |
| 7 | Generator `name` == `qa-generator` | `test_c7_generator_name_is_pinned_value` |
| 8 | Names collide with none of {tpm,tester,developer,reviewer,git-deployer} | `test_c8_names_do_not_collide_with_harness_roles` |
| 9 | PRODUCT_AGENT markers present (exact literals) | `test_c9_product_agent_markers_present` |
| 10 | Each file self-identifies as product agent | `test_c10_each_file_self_identifies_as_product_agent` |
| 11 | Five harness role files unchanged (present, original names; product names absent) | `test_c11_harness_role_files_unchanged_and_present` |
| 12 | Both reference `agent_config/qa_system_prompt.md` | `test_c12_both_reference_qa_system_prompt_path` |
| 13 | Both reference reliability rules (`reliability`) | `test_c13_both_reference_reliability_rules` |
| 14 | Both reference `Playwright MCP` + `connectors/mcp/playwright.mcp.json` + `snapshot` | `test_c14_both_reference_mcp_dom_snapshot_grounding` |
| 15 | Planner produces a structured `test plan` | `test_c15_planner_produces_structured_test_plan` |
| 16 | Planner references `BRD` + `structured` + `field` | `test_c16_planner_references_brd_and_seven_structured_fields` |
| 17 | Generator consumes `plan`; outputs `TypeScript`/`Playwright`/`API` | `test_c17_generator_consumes_plan_outputs_ts_playwright_api` |
| 18 | Roles distinct (each carries only its own marker) | `test_c18_generator_and_planner_roles_are_distinct` (+ 9, 15, 17) |
| 19 | Doc names both paths, both names, product distinction, bound prompt | `test_c19_doc_names_both_agents_and_distinction` |
| 20 | Deterministic committed bytes | `test_c20_committed_files_are_deterministic` |
| 21 | Correct homes + runnable static tests | `test_c21_artifacts_live_at_pinned_homes` (placement); whole suite is static & runs via `uv run pytest agent_config/tests -q` |
| 22 | No regressions | Not a per-file assertion — verified by running the pre-existing `agent_config/tests` + `connectors/` suites (see below); C11 guards the harness-role files specifically. |

## Assumptions recorded

- **Manual frontmatter parse.** The repo has no PyYAML dependency (`uv run python -c "import yaml"`
  → ModuleNotFoundError), and the spec forbids adding one in a test. The `.claude/agents/*.md`
  frontmatter is a flat `key: value` block delimited by `---` fences (confirmed against the shape of
  the existing `tpm.md` header, read only for its fence/field shape — not the product implementation).
  `_parse_frontmatter` splits on the leading fences and reads `key: value` lines. Nested/quoted YAML
  is not required by the pinned fields (`name`, `description`, `tools` are scalars).
- **C11 passes at red time by design.** It is an invariant ("harness role files unchanged") that must
  hold before and after implementation; it passes now (1 passed) and must keep passing. Its failure
  would signal a regression, not missing product work.
- **C22 (no regressions)** is validated by executing the existing suites, not by a new assertion, to
  keep the new module purely static and free of subprocess/network activity.
- **C10 / C18 distinctness** is enforced via the pinned `PRODUCT_AGENT` markers + the case-insensitive
  `product` token + the role-specific content substrings (C15 plan vs C17 tests), per the spec's
  test-binding tokens; the free prose wording is left to the developer/reviewer.

## Red run output (new suite)

```
$ uv run pytest agent_config/tests/test_product_agents.py -q
...
E   FileNotFoundError: [Errno 2] No such file or directory:
    '/.../.claude/agents/qa-planner.md'
...
20 failed, 1 passed in 0.20s
```

Failures are legitimate red: the two agent files and the doc do not exist yet, so presence/parse/
marker/reference/role/doc/determinism/placement checks fail at read time or on missing tokens. The
single pass (C11) is the harness-role invariant described above.

## No-regression check (existing suites still green)

```
$ uv run pytest agent_config/tests/test_qa_system_prompt.py connectors -q
111 passed, 1 skipped in 1.83s
```
