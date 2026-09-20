"""Quality eval against the real model. Excluded from the normal suite.

Run it with `make eval` before changing the prompt, the model, or the merge
logic. It is deliberately not in CI: it needs real credentials, costs real
calls, and is not deterministic, so a red run in CI would mean "the model
rolled badly today" as often as "you broke something".

What it asserts are *properties checkable against the document itself* --
is this quote really in the text, does the explanation name this amount, did
the safety net fire -- never equality with a fixed expected output, which no
stochastic model would reproduce and which would measure nothing useful.

Results are compared against tests/eval/baseline.json: a property that held
when the baseline was recorded and doesn't hold now is a regression. Refresh
the baseline deliberately with `make eval-update` once you've read the diff.
"""

import json
import os
from pathlib import Path

import pytest

from src.api.config import get_settings
from src.api.dependencies import get_pipeline
from tests.eval.cases import CASES, EvalCase

pytestmark = pytest.mark.live

BASELINE_PATH = Path(__file__).parent / "baseline.json"
LAST_RUN_PATH = Path(__file__).parent / "last_run.json"
# A property is boolean, so any drop is a regression. Coverage is a ratio and
# moves with the model's mood, so it gets room before it counts as one.
COVERAGE_TOLERANCE = 0.15


def _evaluate(case: EvalCase, pipeline) -> dict:
    analysis, _ = pipeline.run_with_analysis(
        file_bytes=case.text.encode(),
        filename=f"{case.id}.txt",
        content_type="text/plain",
        language=case.language,
    )

    fired_rules = {flag.rule_id for flag in analysis.red_flags if flag.rule_id}
    quoted = [flag for flag in analysis.red_flags if flag.quote]
    explanation = f"{analysis.plain_explanation}\n{analysis.summary}"

    properties = {
        # Every surviving quote must be findable in the document, or the
        # highlighting it exists for silently does nothing.
        "quotes_grounded": all(flag.quote in case.text for flag in quoted),
        # Each deterministic check may contribute at most one flag: two would
        # mean the rule/LLM merge left a duplicate. (Two *model* findings
        # quoting one sentence is fine -- one passage can carry two risks.)
        "each_rule_appears_once": len(fired_rules) == len([f for f in analysis.red_flags if f.rule_id]),
        "required_rules_fired": case.required_rule_ids <= fired_rules,
        "forbidden_rules_silent": not (case.forbidden_rule_ids & fired_rules),
        "explanation_is_specific": all(m in explanation for m in case.must_mention),
    }
    if case.expected_contexts:
        properties["context_plausible"] = analysis.detected_context in case.expected_contexts
    if case.requires_any_flag:
        properties["raised_a_flag"] = bool(analysis.red_flags)

    return {
        "properties": properties,
        "context": analysis.detected_context,
        "fired_rules": sorted(fired_rules),
        # Share of findings that kept usable evidence. Not pass/fail: it is
        # the number that shows explainability degrading slowly.
        "quote_coverage": round(len(quoted) / len(analysis.red_flags), 3) if analysis.red_flags else 1.0,
        "flags": len(analysis.red_flags),
        "titles": sorted(flag.title for flag in analysis.red_flags),
    }


def test_live_quality_has_not_regressed():
    if get_settings().is_demo_mode:
        pytest.skip("no real AI provider configured — this eval would grade the demo client")

    pipeline = get_pipeline()
    results = {case.id: _evaluate(case, pipeline) for case in CASES}
    LAST_RUN_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if os.environ.get("UPDATE_EVAL_BASELINE") == "1":
        BASELINE_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        pytest.skip(f"baseline updated at {BASELINE_PATH}")

    failures = [
        f"{case_id}.{name}"
        for case_id, result in results.items()
        for name, passed in result["properties"].items()
        if not passed
    ]
    assert not failures, f"properties not holding: {failures}\nfull run written to {LAST_RUN_PATH}"

    if not BASELINE_PATH.exists():
        pytest.fail(f"no baseline yet — record one with `make eval-update` (run written to {LAST_RUN_PATH})")

    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    regressions = []
    for case_id, result in results.items():
        previous = baseline.get(case_id)
        if previous is None:
            continue
        for name, passed in previous["properties"].items():
            if passed and not result["properties"].get(name, False):
                regressions.append(f"{case_id}.{name}")
        drop = previous["quote_coverage"] - result["quote_coverage"]
        if drop > COVERAGE_TOLERANCE:
            regressions.append(
                f"{case_id}.quote_coverage {previous['quote_coverage']} -> {result['quote_coverage']}"
            )

    assert not regressions, f"regressions against baseline: {regressions}\nfull run written to {LAST_RUN_PATH}"
