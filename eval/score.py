#!/usr/bin/env python
"""Eval scorer for unit ``p0-eval-harness`` — the reliability measurement gate.

Runs the hand-written **baseline** TS-Playwright suite (``reference_app/e2e/tests/eval``,
driven by ``playwright.eval.config.ts``) against the **clean** reference app and each of
the three injected-bug variants (selected by the ``EVAL_BUG`` env var, served by
``eval/buggy_backend.py``), with **re-runs**, and computes the four Phase-0 reliability
metrics with the pinned definitions from ``.harness/tasks/p0-eval-harness.md``:

  * ``bug_catch_rate``               = (# buggy variants caught) / (# buggy variants)
  * ``false_positive_rate``          = (# baseline tests that fail on clean) / (# tests on clean)
  * ``flake_rate``                   = (# flaky (variant,test) pairs) / (# pairs evaluated)
  * ``assertion_meaningfulness_rate``= (# meaningful tests) / (# baseline tests)

where a buggy variant is *caught* if >=1 baseline test fails on it, and a test is
*meaningful* if it passes on clean AND fails on >=1 buggy variant.

Usage (from the repo root)::

    uv run python eval/score.py [--reruns N] [--json]

Options:
  --reruns N   re-runs per variant for flake detection (int, default 2, N >= 2).
  --json       ALSO emit a machine-readable JSON object (with a ``metrics`` field
               carrying the four numeric 0..1 keys + a per-variant / per-test
               breakdown) to stdout, in addition to the always-printed human table.

Exit code (Phase-0 sanity gate): ``0`` iff the harness ran to completion AND
``bug_catch_rate == 1.0`` AND ``false_positive_rate == 0.0`` AND ``flake_rate == 0.0``;
otherwise non-zero. The metrics are printed BEFORE exiting, in either case.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile

# --------------------------------------------------------------------------- paths / constants

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
E2E_DIR = REPO_ROOT / "reference_app" / "e2e"
EVAL_CONFIG = "playwright.eval.config.ts"

BACKEND_PORT = 8000
FRONTEND_PORT = 5173

CLEAN_VARIANT = "none"
BUGGY_VARIANTS = ("checkout_total", "cart_quantity", "order_auth_bypass")
ALL_VARIANTS = (CLEAN_VARIANT, *BUGGY_VARIANTS)

METRIC_NAMES = (
    "bug_catch_rate",
    "false_positive_rate",
    "flake_rate",
    "assertion_meaningfulness_rate",
)


# --------------------------------------------------------------------------- process helpers


def _kill_port(port: int) -> None:
    """Best-effort kill of anything listening on ``port`` so launches never collide."""
    try:
        out = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except Exception:
        return
    for pid in out.split():
        with contextlib.suppress(Exception):
            os.kill(int(pid), signal.SIGKILL)


def _run_baseline_once(variant: str, timeout: int = 300) -> dict[str, bool]:
    """Run the baseline suite once against ``variant`` and return {test_id: passed}.

    Uses Playwright's JSON reporter written to a temp file (so webServer stdout can
    never corrupt the parse). ``variant == "none"`` means the selector is unset
    (clean). Raises ``RuntimeError`` on an infrastructure failure (no report / no
    tests) so the caller can mark the harness incomplete.
    """
    _kill_port(BACKEND_PORT)
    _kill_port(FRONTEND_PORT)

    env = os.environ.copy()
    if variant == CLEAN_VARIANT:
        env.pop("EVAL_BUG", None)
    else:
        env["EVAL_BUG"] = variant

    with tempfile.NamedTemporaryFile(
        suffix=".json", prefix="pw-eval-", delete=False
    ) as tf:
        report_path = tf.name
    env["PLAYWRIGHT_JSON_OUTPUT_NAME"] = report_path

    try:
        subprocess.run(
            [
                "npx",
                "playwright",
                "test",
                "--config",
                EVAL_CONFIG,
                "--reporter=json",
            ],
            cwd=str(E2E_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        # Playwright exits non-zero on test failures (expected for buggy variants);
        # the source of truth is the JSON report, not the exit code.
        try:
            report = json.loads(pathlib.Path(report_path).read_text())
        except Exception as exc:  # pragma: no cover - infra failure path
            raise RuntimeError(
                f"baseline run for variant {variant!r} produced no parseable JSON report: {exc}"
            )
    finally:
        with contextlib.suppress(Exception):
            os.unlink(report_path)
        _kill_port(BACKEND_PORT)
        _kill_port(FRONTEND_PORT)

    results: dict[str, bool] = {}
    _collect_specs(report.get("suites", []), results)
    if not results:
        raise RuntimeError(
            f"baseline run for variant {variant!r} reported zero tests (infra failure)"
        )
    return results


def _collect_specs(suites: list, acc: dict[str, bool]) -> None:
    """Recursively flatten a Playwright JSON report to {test_id: passed}."""
    for suite in suites:
        file = suite.get("file", "")
        for spec in suite.get("specs", []):
            title = spec.get("title", "")
            test_id = f"{file}::{title}"
            # A spec is "passed" iff Playwright marks it ok AND every test result is
            # a pass (defensive: fall back to inspecting the results array).
            ok = bool(spec.get("ok", False))
            statuses = [
                r.get("status")
                for t in spec.get("tests", [])
                for r in t.get("results", [])
            ]
            if statuses:
                ok = ok and all(s == "passed" for s in statuses)
            acc[test_id] = ok
        _collect_specs(suite.get("suites", []), acc)


# --------------------------------------------------------------------------- scoring


def run_all(reruns: int) -> dict:
    """Run every variant ``reruns`` times and compute the four metrics + breakdown."""
    # runs[variant] = list of {test_id: passed} (one dict per re-run)
    runs: dict[str, list[dict[str, bool]]] = {v: [] for v in ALL_VARIANTS}
    completed = True
    errors: list[str] = []

    for variant in ALL_VARIANTS:
        for _ in range(reruns):
            try:
                runs[variant].append(_run_baseline_once(variant))
            except RuntimeError as exc:
                completed = False
                errors.append(str(exc))

    # Canonical baseline test set: the union of test ids seen on the clean variant.
    baseline_tests: set[str] = set()
    for run in runs[CLEAN_VARIANT]:
        baseline_tests.update(run.keys())
    # Fall back to any variant if clean produced nothing (harness incomplete).
    if not baseline_tests:
        for variant in ALL_VARIANTS:
            for run in runs[variant]:
                baseline_tests.update(run.keys())
    tests = sorted(baseline_tests)

    def passed(variant: str, run_idx: int, test_id: str) -> bool:
        run = runs[variant][run_idx]
        return bool(run.get(test_id, False))

    def failed_any_run(variant: str, test_id: str) -> bool:
        return any(
            not passed(variant, i, test_id) for i in range(len(runs[variant]))
        )

    def passed_all_runs(variant: str, test_id: str) -> bool:
        return len(runs[variant]) > 0 and all(
            passed(variant, i, test_id) for i in range(len(runs[variant]))
        )

    # ---- bug_catch_rate ----
    caught = {}
    for variant in BUGGY_VARIANTS:
        caught[variant] = any(failed_any_run(variant, t) for t in tests) and bool(
            runs[variant]
        )
    bug_catch_rate = (
        sum(1 for v in BUGGY_VARIANTS if caught[v]) / len(BUGGY_VARIANTS)
        if BUGGY_VARIANTS
        else 0.0
    )

    # ---- false_positive_rate (clean variant) ----
    clean_fail_count = sum(1 for t in tests if failed_any_run(CLEAN_VARIANT, t))
    false_positive_rate = (clean_fail_count / len(tests)) if tests else 0.0

    # ---- flake_rate (all variants x all baseline tests) ----
    flaky_pairs = 0
    total_pairs = 0
    for variant in ALL_VARIANTS:
        for t in tests:
            verdicts = [passed(variant, i, t) for i in range(len(runs[variant]))]
            if not verdicts:
                continue
            total_pairs += 1
            if len(set(verdicts)) > 1:
                flaky_pairs += 1
    flake_rate = (flaky_pairs / total_pairs) if total_pairs else 0.0

    # ---- assertion_meaningfulness_rate ----
    meaningful: list[str] = []
    non_meaningful: list[str] = []
    for t in tests:
        passes_clean = passed_all_runs(CLEAN_VARIANT, t)
        detects_bug = any(failed_any_run(v, t) for v in BUGGY_VARIANTS)
        if passes_clean and detects_bug:
            meaningful.append(t)
        else:
            non_meaningful.append(t)
    assertion_meaningfulness_rate = (
        (len(meaningful) / len(tests)) if tests else 0.0
    )

    metrics = {
        "bug_catch_rate": round(bug_catch_rate, 6),
        "false_positive_rate": round(false_positive_rate, 6),
        "flake_rate": round(flake_rate, 6),
        "assertion_meaningfulness_rate": round(assertion_meaningfulness_rate, 6),
    }

    # Per-variant / per-test breakdown for the JSON report.
    variants_breakdown = {}
    for variant in ALL_VARIANTS:
        per_test = {
            t: [passed(variant, i, t) for i in range(len(runs[variant]))]
            for t in tests
        }
        entry = {"runs": len(runs[variant]), "tests": per_test}
        if variant in BUGGY_VARIANTS:
            entry["caught"] = bool(caught[variant])
        variants_breakdown[variant] = entry

    gate = (
        completed
        and metrics["bug_catch_rate"] == 1.0
        and metrics["false_positive_rate"] == 0.0
        and metrics["flake_rate"] == 0.0
    )

    return {
        "reruns": reruns,
        "completed": completed,
        "errors": errors,
        "metrics": metrics,
        "variants": variants_breakdown,
        "meaningfulness_audit": {
            "meaningful": meaningful,
            "non_meaningful": non_meaningful,
        },
        "gate_passed": bool(gate),
        "_tests": tests,
        "_caught": caught,
    }


# --------------------------------------------------------------------------- reporting


def print_table(report: dict) -> None:
    m = report["metrics"]
    tests = report["_tests"]
    caught = report["_caught"]

    print("=" * 72)
    print("Eval reliability metrics  (unit p0-eval-harness)")
    print(f"  re-runs per variant : {report['reruns']}")
    print(f"  baseline tests      : {len(tests)}")
    print(f"  harness completed   : {report['completed']}")
    print("-" * 72)
    print("Metrics:")
    print(f"  bug_catch_rate                = {m['bug_catch_rate']:.3f}")
    print(f"  false_positive_rate           = {m['false_positive_rate']:.3f}")
    print(f"  flake_rate                    = {m['flake_rate']:.3f}")
    print(
        f"  assertion_meaningfulness_rate = {m['assertion_meaningfulness_rate']:.3f}"
    )
    print("-" * 72)
    print("Per-variant caught / not-caught:")
    for variant in BUGGY_VARIANTS:
        mark = "CAUGHT" if caught.get(variant) else "NOT CAUGHT"
        print(f"  {variant:<20} : {mark}")
    print(f"  {CLEAN_VARIANT:<20} : (clean baseline — no fault; false-positive check)")
    print("-" * 72)
    print("Assertion-meaningfulness audit (a test is meaningful if it passes on")
    print("clean AND fails on >=1 buggy variant):")
    audit = report["meaningfulness_audit"]
    for t in audit["meaningful"]:
        print(f"  [meaningful]     {t}")
    for t in audit["non_meaningful"]:
        print(f"  [non-meaningful] {t}")
    if not audit["non_meaningful"]:
        print("  (all baseline tests are meaningful / discriminating)")
    if report["errors"]:
        print("-" * 72)
        print("Harness errors:")
        for e in report["errors"]:
            print(f"  ! {e}")
    print("=" * 72)


def public_report(report: dict) -> dict:
    """Strip private ``_`` keys for the machine-readable JSON emission."""
    return {k: v for k, v in report.items() if not k.startswith("_")}


# --------------------------------------------------------------------------- CLI


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Eval reliability scorer.")
    parser.add_argument(
        "--reruns",
        type=int,
        default=2,
        help="re-runs per variant for flake detection (default 2, minimum 2).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="also emit a machine-readable JSON object to stdout.",
    )
    args = parser.parse_args(argv)

    if args.reruns < 2:
        parser.error("--reruns must be >= 2")

    report = run_all(args.reruns)

    # Always print the human-readable table first.
    print_table(report)

    # Optionally emit the machine-readable JSON (single compact object).
    if args.json:
        print(json.dumps(public_report(report)))

    return 0 if report["gate_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
