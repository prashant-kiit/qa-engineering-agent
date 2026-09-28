# Test coverage — `p1-qa-system-prompt` (TDD red)

Static acceptance suite for the generic QA system prompt content artifact. All checks are
presence / shape / marker / generic-safety assertions on the committed text files — **no** model
call, agent run, browser, or network I/O.

- **Test file:** `agent_config/tests/test_qa_system_prompt.py`
- **Run:** `uv run pytest agent_config/tests -q`
- No `agent_config/tests/__init__.py` added — the connectors suite runs without one, and the test
  filename `test_qa_system_prompt.py` is unique, so pytest import collection needs no package init.
- Implementation was **not** read (unbiased). Pinned literals below come only from the spec's
  Interfaces §Paths / §Markers.

## Criterion → test mapping

| # | Acceptance criterion | Test(s) |
|---|---|---|
| 1 | Prompt file present, non-empty, valid UTF-8 at `agent_config/qa_system_prompt.md` | `test_c1_prompt_file_present_and_nonempty_utf8` |
| 2 | `agent_config/README.md` present + non-empty | `test_c2_readme_present_and_nonempty` |
| 3 | Exact version marker `<!-- QA_SYSTEM_PROMPT_VERSION: v1 -->` | `test_c3_version_marker_v1_exact_literal` |
| 4 | Persona section anchor `<!-- SECTION: PERSONA -->` + content | `test_c4_persona_section_anchor_present` |
| 5 | Methodology section anchor `<!-- SECTION: METHODOLOGY -->` + content | `test_c5_methodology_section_anchor_present` |
| 6 | Reliability-rules section anchor `<!-- SECTION: RELIABILITY_RULES -->` | `test_c6_reliability_rules_section_anchor_present` |
| 7 | DOM-grounding rule `<!-- RULE: DOM_GROUNDING -->` | `test_c7_dom_grounding_rule_present` |
| 8 | Meaningful-assertions rule `<!-- RULE: MEANINGFUL_ASSERTIONS -->` | `test_c8_meaningful_assertions_rule_present` |
| 9 | API-cross-check rule `<!-- RULE: API_CROSS_CHECK -->` | `test_c9_api_cross_check_rule_present` |
| 10 | Heal-vs-regression rule `<!-- RULE: HEAL_VS_REGRESSION -->` | `test_c10_heal_vs_regression_rule_present` |
| 11 | Untrusted-app-content rule `<!-- RULE: UNTRUSTED_APP_CONTENT -->` | `test_c11_untrusted_app_content_rule_present` |
| 12 | All five rule anchors present (none omitted) | `test_c12_all_five_reliability_rule_anchors_present` |
| 13 | Structured-fields reference `<!-- SECTION: STRUCTURED_FIELDS_REF -->` (+ "seven"/"structured field" + "BRD") | `test_c13_structured_fields_reference_present` |
| 14 | BRD-injection section anchor `<!-- SECTION: BRD_INJECTION -->` | `test_c14_brd_injection_section_anchor_present` |
| 15 | `{{BRD}}` appears exactly once, inside the BRD-injection section | `test_c15_brd_placeholder_present_exactly_once_in_section` |
| 16 | Injection slot carries no baked tenant/target content | `test_c16_brd_injection_section_has_no_baked_tenant_content` |
| 17 | No target-specific content (URLs / credential values) in prompt | `test_c17_prompt_has_no_target_specific_content` |
| 18 | No secrets in prompt or README | `test_c18_no_secrets_in_prompt_or_readme` |
| 19 | README documents prompt path, `v1`, `{{BRD}}` | `test_c19_readme_documents_contract` |
| 20 | Deterministic static bytes (read twice = identical) | `test_c20_committed_files_are_deterministic` |
| 21 | Correct home under `agent_config/`; static-only tests | `test_c21_artifacts_live_under_agent_config` (+ the suite itself does no model/agent/browser/network I/O) |
| 22 | No regressions (connectors + Phase 0 suites still pass) | Verified out-of-band: `uv run pytest connectors/tests -q` → 90 passed, 1 skipped. This unit adds only tests under `agent_config/`. |

## Assumptions / interpretations (spec leaves prose to developer)

- **Anchor presence, not prose.** Per Interfaces §Markers the Tester asserts anchor *presence* (and
  for version/`{{BRD}}` the exact form + count). Rule/section prose wording is the developer's and is
  judged by the reviewer — tests do not pin sentence content beyond the documented tokens.
- **C13 tokens.** Spec says the Tester asserts the anchor + "seven"/"structured fields" + "BRD"
  references. Implemented case-insensitively within the section slice, accepting either "seven" or
  "structured field"; no field-schema table is required (fields live in the unit-2 config).
- **C4/C5 "non-trivial content".** Asserted as: text exists between the section anchor and the next
  `<!-- SECTION:` anchor (non-empty slice). Exact length/quality is the reviewer's call.
- **Generic-safety forbidden tokens (C16/17/18).** Substring checks for `127.0.0.1:5173`,
  `127.0.0.1:8000`, bare `:5173`/`:8000`, `testuser`, `testpass` — the reference-app specifics named
  in the spec. This is a best-effort denylist of the spec-named values, not an exhaustive secret
  scanner.
- **C22** is a repo-wide no-regression criterion; covered by running the connectors suite (green) and
  confirming this change is additive under `agent_config/` only.

## Red run (legitimate — missing artifact)

`uv run pytest agent_config/tests -q`:

```
21 failed in 0.21s
```

All 21 fail because `agent_config/qa_system_prompt.md` / `agent_config/README.md` do not exist yet —
i.e. `FileNotFoundError` on read and `is_file()`/marker assertions failing. Representative:

```
FileNotFoundError: [Errno 2] No such file or directory:
  '.../agent_config/qa_system_prompt.md'
...
E   AssertionError: assert (False)   # PROMPT_PATH.is_file()
```

This is red for the right reason (missing behavior/artifact), not a harness/import error.

## No-regression check

`uv run pytest connectors/tests -q` → **90 passed, 1 skipped** (unchanged). The connectors suite was
not touched.
