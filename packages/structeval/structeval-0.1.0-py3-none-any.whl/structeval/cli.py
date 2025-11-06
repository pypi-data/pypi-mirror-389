from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from structeval.exceptions import ValidationError
from structeval.models.compare_result import CompareResult
from structeval.models.eval_config import EvalConfig
from structeval.reporting.html import HtmlReporter
from structeval.reporting.text import TextReporter
from structeval.struct_evaluator import StructEvaluator


def _load_json_arg(value: str) -> Any:
    if value == "-":
        return json.load(sys.stdin)
    path = Path(value)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _produce_report(result: CompareResult, beta: float, report_type: str) -> str:
    if report_type == "text":
        return TextReporter().report(result, beta)
    elif report_type == "html":
        return HtmlReporter().report(result, beta)
    elif report_type == "json":
        output_dict = result.model_dump()
        output_dict["sum_metrics"][f"f{beta}_score"] = result.sum_metrics.f_score(beta)
        return json.dumps(output_dict, indent=2)
    else:
        raise ValueError(f"Unsupported report type: {report_type}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="structeval",
        description="Compare two JSON-like structures and report similarity metrics.",
    )
    parser.add_argument("--test", required=True, help="Path to test JSON file or '-' for stdin")
    parser.add_argument("--gt", required=True, help="Path to ground truth JSON file or '-' for stdin")
    parser.add_argument("--schema", help="Optional JSON Schema file to drive field-specific evaluators")
    parser.add_argument(
        "--config",
        help="Optional evaluation config file (JSON). Specifies the evaluation rules for each field type.",
    )
    parser.add_argument("--beta", type=float, default=1, help="Beta value for F-score calculation")
    # Reporting
    parser.add_argument("--report", choices=["text", "html", "json"], default="text", help="Report format")
    parser.add_argument(
        "--color/--no-color",
        dest="color",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Colorize text output",
    )

    args = parser.parse_args(argv)

    try:
        test_value = _load_json_arg(args.test)
        ground_truth_value = _load_json_arg(args.gt)  # type: ignore[index]
    except Exception as exc:  # pragma: no cover - user input path errors
        print(f"Error loading input: {exc}", file=sys.stderr)
        return 2

    json_schema = None
    if args.schema:
        try:
            json_schema = _load_json_arg(args.schema)
        except Exception as exc:  # pragma: no cover
            print(f"Error loading schema: {exc}", file=sys.stderr)
            return 2

    config = EvalConfig.from_file(args.config) if args.config else None

    # Run comparison
    try:
        result = StructEvaluator.run(
            test_value=test_value,
            ground_truth_value=ground_truth_value,
            json_schema=json_schema,
            configuration=config,
        )
    except ValidationError as exc:
        sys.stdout.write(f"Error: {exc}")
        return 2

    # Reporting
    report_output = _produce_report(result, args.beta, args.report)
    sys.stdout.write(report_output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
