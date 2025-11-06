from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

from structeval.models.compare_result import ComparedArray, ComparedElement, ComparedObject, CompareResult
from structeval.models.sum_metrics import SumMetrics


@dataclass
class _TreeNode:  # legacy placeholder; no longer used in new renderer
    scalars: list = field(default_factory=list)
    arrays: list = field(default_factory=list)
    children: dict[str, _TreeNode] = field(default_factory=dict)


class HtmlReporter:
    def __init__(self) -> None:
        pass

    def _style(self) -> str:
        return (
            "<style>\n"
            "body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial,sans-serif;color:#1f2937;line-height:1.4;margin:1rem;}\n"
            ".summary{display:flex;gap:1rem;flex-wrap:wrap;margin:0 0 1rem 0;}\n"
            ".chip{background:#eef2ff;color:#3730a3;padding:.25rem .5rem;border-radius:.5rem;font-weight:600;}\n"
            "details{margin:.5rem 0 0.75rem 0;}\n"
            "details>summary{cursor:pointer;font-weight:700;}\n"
            "table{border-collapse:collapse;width:100%;table-layout:fixed;margin:.5rem 0;border:1px solid #e5e7eb;}\n"
            "th,td{border:1px solid #e5e7eb;padding:.4rem .5rem;vertical-align:top;word-wrap:break-word;white-space:pre-wrap;}\n"
            "th{background:#f3f4f6;color:#111827;text-align:left;}\n"
            ".path{color:#7c3aed;font-weight:600;}\n"
            ".score{font-variant-numeric:tabular-nums;font-weight:700;}\n"
            ".score.good{color:#059669}.score.mid{color:#d97706}.score.bad{color:#dc2626}\n"
            ".idx{color:#2563eb;font-weight:600;}\n"
            ".section{margin-top:1rem;}\n"
            "</style>\n"
        )

    def _score_class(self, score: float) -> str:
        if score >= 0.8:
            return "good"
        if score >= 0.4:
            return "mid"
        return "bad"

    def _summary(self, result: SumMetrics, beta: float) -> str:
        chips = [
            f"<span class='chip'>TP (weighted): {result.true_positives:.2f}</span>",
            f"<span class='chip'>Actual Positives: {result.positive_predictions}</span>",
            f"<span class='chip'>GT Positives: {result.ground_truth_predictions}</span>",
            f"<span class='chip'>Precision: {result.precision:.2f}</span>",
            f"<span class='chip'>Recall: {result.recall:.2f}</span>",
            f"<span class='chip'>F{beta}: {result.f_score(beta):.2f}</span>",
        ]
        return "<div class='summary'>" + "".join(chips) + "</div>\n"

    def _inline_summary_text(self, result: SumMetrics, beta: float) -> str:
        return f" [P {result.precision:.2f} · R {result.recall:.2f} · F{beta} {result.f_score(beta):.2f}]"

    def _object_table_rows(self, obj: ComparedObject) -> list[str]:
        rows: list[str] = []
        for k in sorted(obj.properties.keys()):
            v = obj.properties[k]
            if isinstance(v, ComparedElement):
                rows.append(
                    "<tr>"
                    f"<td class='path'>{escape(k)}</td>"
                    f"<td>{escape(str(v.test_value))}</td>"
                    f"<td>{escape(str(v.ground_truth_value))}</td>"
                    f"<td class='score {self._score_class(v.score)}'>{v.score:.2f}</td>"
                    f"<td>{escape(v.method)}</td>"
                    "</tr>"
                )
        return rows

    def _collect_rows_from_output(self, out, prefix: str = "") -> list[list[str]]:
        rows: list[list[str]] = []
        if isinstance(out, ComparedElement):
            field = prefix or "*"
            rows.append([field, str(out.test_value), str(out.ground_truth_value), f"{out.score:.2f}", out.method])
            return rows
        if isinstance(out, ComparedObject):
            for k in sorted(out.properties.keys()):
                rows += self._collect_rows_from_output(out.properties[k], f"{prefix}.{k}" if prefix else k)
            return rows
        if isinstance(out, ComparedArray):
            for elem in out.present_items:
                idx_prefix = f"{prefix}[{elem.current_index}]" if prefix else f"[{elem.current_index}]"
                rows += self._collect_rows_from_output(elem.values, idx_prefix)
            for miss in out.missing_items:
                miss_field = f"{prefix}[{miss.target_index}]" if prefix else f"[{miss.target_index}]"
                rows.append([f"{miss_field} <missing>", "", str(miss.value), "", ""])
            return rows
        return rows

    def _render_array_table(self, arr: ComparedArray, title: str, beta: float) -> str:
        headers = "<thead><tr><th>idx0</th><th>idx1</th><th>field</th><th>actual</th><th>ground truth</th><th>score</th><th>method</th></tr></thead>"
        body_rows: list[str] = []
        for i, elem in enumerate(arr.present_items):
            elem_rows = self._collect_rows_from_output(elem.values)
            target = "" if elem.target_index is None else str(elem.target_index)
            if not elem_rows:
                body_rows.append(f"<tr><td class='idx'>{i}</td><td class='idx'>{escape(target)}</td><td class='path'>*</td><td></td><td></td><td></td><td></td></tr>")
            else:
                for j, r in enumerate(elem_rows):
                    idx0 = str(i) if j == 0 else ""
                    idx1 = target if j == 0 else ""
                    field, actual, expected, score, method = r
                    prefix = f"[{i}]"
                    if field.startswith(prefix):
                        field = field[len(prefix) :].lstrip(".")
                    # determine score class defensively
                    try:
                        cls = self._score_class(float(score))
                    except Exception:
                        cls = ""
                    body_rows.append(
                        "<tr>"
                        f"<td class='idx'>{escape(idx0)}</td>"
                        f"<td class='idx'>{escape(idx1)}</td>"
                        f"<td class='path'>{escape(field)}</td>"
                        f"<td>{escape(actual)}</td>"
                        f"<td>{escape(expected)}</td>"
                        f"<td class='score{(' ' + cls) if cls else ''}'>{escape(str(score))}</td>"
                        f"<td>{escape(method)}</td>"
                        "</tr>"
                    )
            if i < len(arr.present_items) - 1:
                body_rows.append("<tr><td colspan='7' style='border:none'>&nbsp;</td></tr>")
        for m in arr.missing_items:
            body_rows.append(
                "<tr>"
                "<td class='idx'></td>"
                f"<td class='idx'>{escape(str(m.target_index))}</td>"
                "<td class='path'>&lt;missing&gt;</td>"
                "<td></td>"
                f"<td>{escape(str(m.value))}</td>"
                "<td></td><td></td>"
                "</tr>"
            )
        inline = self._inline_summary_text(arr.sum_metrics, beta)
        return f"<details open><summary>{escape(title)} []{escape(inline)}</summary><table>{headers}<tbody>{''.join(body_rows)}</tbody></table></details>"

    def _render_object_tables(self, obj: ComparedObject, title: str, beta: float) -> str:
        parts: list[str] = []
        rows = self._object_table_rows(obj)
        if rows:
            parts.append(
                f"<details open><summary>{escape(title)}{escape(self._inline_summary_text(obj.sum_metrics, beta))}</summary>"
                "<table>"
                "<thead><tr><th>field</th><th>actual</th><th>ground truth</th><th>score</th><th>method</th></tr></thead>"
                f"<tbody>{''.join(rows)}</tbody>"
                "</table>"
                "</details>"
            )
        for k in sorted(obj.properties.keys()):
            v = obj.properties[k]
            if isinstance(v, ComparedObject):
                parts.append(self._render_object_tables(v, f"{title}.{k}" if title else k, beta))
            elif isinstance(v, ComparedArray):
                parts.append(self._render_array_table(v, f"{title}.{k}" if title else k, beta))
        return "".join(parts)

    def report(self, comparison_output: CompareResult, beta: float = 1) -> str:
        body = ""
        root = comparison_output.output
        if isinstance(root, ComparedObject):
            body = self._render_object_tables(root, "Root", beta)
        elif isinstance(root, ComparedArray):
            body = self._render_array_table(root, "Root", beta)
        elif isinstance(root, ComparedElement):
            rows = (
                "<tr>"
                "<td class='path'>$</td>"
                f"<td>{escape(str(root.test_value))}</td>"
                f"<td>{escape(str(root.ground_truth_value))}</td>"
                f"<td class='score {self._score_class(root.score)}'>{root.score:.2f}</td>"
                f"<td>{escape(root.method)}</td>"
                "</tr>"
            )
            body = (
                "<details open><summary>Root</summary><table>"
                "<thead><tr><th>field</th><th>actual</th><th>ground truth</th><th>score</th><th>method</th></tr></thead>"
                f"<tbody>{rows}</tbody></table></details>"
            )
        return (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"{self._style()}"
            "</head><body>"
            f"{self._summary(comparison_output.sum_metrics, beta)}"
            f"{body}"
            "</body></html>"
        )
