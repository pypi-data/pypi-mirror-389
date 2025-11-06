from __future__ import annotations

from structeval.reporting.html import HtmlReporter
from structeval.reporting.text import TextReporter
from structeval.struct_evaluator import StructEvaluator

LEFT = {
    "name": "John",
    "age": 25,
    "is_student": True,
    "metadata": {"had_a_meal": True, "nested_metadata": {"had_a_meal_yesterday": True}},
    "hobbies": [
        {"name": "reading", "is_physical": False, "metadata": {"is_true": True}},
        {"name": "swimming", "is_physical": True, "metadata": {"is_true": True}},
    ],
}

RIGHT = {
    "name": "Jane",
    "age": 26,
    "is_student": True,
    "metadata": {"had_a_meal": True, "nested_metadata": {"had_a_meal_yesterday": True}},
    "hobbies": [
        {"name": "hiking swimming", "is_physical": True, "metadata": {"is_true": True}},
        {"name": "running and doing lots of other things", "is_physical": True, "metadata": {"is_true": True}},
        {"name": "buildings and doing lots of other things", "is_physical": False, "metadata": {"is_true": True}},
    ],
}


def test_smoke_text_reporter_basic_output_without_color() -> None:
    result = StructEvaluator.run(LEFT, RIGHT)
    text = TextReporter(use_color=False).report(result)
    # Header and metrics
    assert "Results" in text


def test_smoke_text_reporter_color_codes_present_when_enabled() -> None:
    result = StructEvaluator.run(LEFT, RIGHT)
    text = TextReporter(use_color=True).report(result)

    # ANSI escape sequences for color should be present
    assert "\x1b[" in text


def test_smoke_html_reporter() -> None:
    result = StructEvaluator.run(LEFT, RIGHT)
    html = HtmlReporter().report(result)

    assert "<!doctype html>" in html.lower()
