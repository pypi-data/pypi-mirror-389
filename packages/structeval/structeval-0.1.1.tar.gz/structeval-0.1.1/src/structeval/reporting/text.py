from __future__ import annotations

import re
import textwrap

from structeval.models.compare_result import ComparedArray, ComparedElement, ComparedObject, CompareResult
from structeval.models.sum_metrics import SumMetrics


class TextReporter:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"

    def __init__(self, use_color: bool = True) -> None:
        self.use_color = use_color
        # default fixed column widths (characters)
        self.column_widths: dict[str, int] = {
            "idx0": 5,
            "idx1": 5,
            "field": 20,
            "left": 28,
            "right": 28,
            "score": 7,
            "method": 18,
        }

    def _c(self, text: str, color: str) -> str:
        if not self.use_color:
            return text
        return f"{color}{text}{self.RESET}"

    def _score_color(self, score: float) -> str:
        if score >= 0.8:
            return self.GREEN
        if score >= 0.4:
            return self.YELLOW
        return self.RED

    def _header(self, result: SumMetrics, beta: float) -> str:
        parts = [
            self._c("TP (weighted)", self.CYAN) + f": {result.true_positives:.2f}",
            self._c("Actual Positives", self.CYAN) + f": {result.positive_predictions:.2f}",
            self._c("GT Positives", self.CYAN) + f": {result.ground_truth_predictions:.2f}",
            self._c("Precision", self.CYAN) + f": {result.precision:.2f}",
            self._c("Recall", self.CYAN) + f": {result.recall:.2f}",
            self._c(f"F{beta}", self.CYAN) + f": {result.f_score(beta):.2f}",
        ]
        return f"{self.BOLD}Results{self.RESET}  " + "  |  ".join(parts)

    def _strip_ansi(self, s: str) -> str:
        return re.sub(r"\x1b\[[0-9;]*m", "", s)

    def _ljust_visible(self, s: str, width: int) -> str:
        visible = self._strip_ansi(s)
        padding = max(0, width - len(visible))
        return s + (" " * padding)

    def _wrap_cell(self, text: str, width: int) -> list[str]:
        # wrap based on visible text width; ignore ANSI during wrapping
        plain = self._strip_ansi(text)
        if plain == "":
            return [""]
        wrapped = textwrap.wrap(plain, width=width, break_long_words=True, replace_whitespace=False)
        return wrapped or [plain]

    def _draw_table(self, headers: list[str], rows: list[list[str]], indent: int = 0, title: str | None = None) -> list[str]:
        pad = " " * indent
        # fixed widths per header
        widths = [self.column_widths.get(h, 20) for h in headers]

        def hline(sep_left: str = "+", sep_mid: str = "+", sep_right: str = "+", fill: str = "-") -> str:
            parts = [fill * (w + 2) for w in widths]
            return pad + sep_left + sep_mid.join(parts) + sep_right

        out: list[str] = []
        if title:
            out.append(pad + self._c(title, self.BOLD))
        out.append(hline())
        # header row (color after padding)
        head_cells = []
        for i, h in enumerate(headers):
            cell = self._ljust_visible(h, widths[i])
            head_cells.append(self._c(cell, self.CYAN))
        head = pad + "|" + "|".join(f" {c} " for c in head_cells) + "|"
        out.append(head)
        out.append(hline(sep_left="+", sep_mid="+", sep_right="+", fill="-"))
        # body with wrapping; apply simple column colorization
        for row in rows:
            wrapped_cols: list[list[str]] = []
            for i, cell in enumerate(row):
                wrapped_cols.append(self._wrap_cell(cell, widths[i]))
            height = max(len(col) for col in wrapped_cols) if wrapped_cols else 1
            for ln in range(height):
                rendered_cells = []
                for i, col_lines in enumerate(wrapped_cols):
                    content = col_lines[ln] if ln < len(col_lines) else ""
                    # Apply color by column
                    col_name = headers[i].lower()
                    if col_name == "field":
                        content = self._c(content, self.MAGENTA)
                    elif col_name == "score":
                        try:
                            color = self._score_color(float(content))
                        except Exception:
                            color = self.DIM
                        content = self._c(content, color)
                    rendered_cells.append(self._ljust_visible(content, widths[i]))
                out.append(pad + "|" + "|".join(f" {c} " for c in rendered_cells) + "|")
        out.append(hline())
        return out

    # ---- Tabular pretty-print of JsonComparisonOutput.output (nested) ----
    def _object_table_rows(self, obj: ComparedObject) -> list[list[str]]:
        rows: list[list[str]] = []
        for k in sorted(obj.properties.keys()):
            v = obj.properties[k]
            if isinstance(v, ComparedElement):
                rows.append([k, str(v.test_value), str(v.ground_truth_value), f"{v.score:.2f}", v.method])
        return rows

    def _collect_rows_from_output(self, out, prefix: str = "") -> list[list[str]]:
        # Flatten fields into rows for array element rendering
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
            # Recurse into each element, prefixing with its index
            for elem in out.present_items:
                idx_prefix = f"{prefix}[{elem.current_index}]" if prefix else f"[{elem.current_index}]"
                rows += self._collect_rows_from_output(elem.values, idx_prefix)
            # Optionally include missing items as rows
            for miss in out.missing_items:
                miss_field = f"{prefix}[{miss.target_index}]" if prefix else f"[{miss.target_index}]"
                rows.append([f"{miss_field} <missing>", "", str(miss.value), "", ""])
            return rows
        # Lists/dicts unlikely here due to Output modeling; ignore otherwise
        return rows

    def _render_object_tables(self, obj: ComparedObject, title: str, indent: int, beta: float) -> list[str]:
        lines: list[str] = []
        rows = self._object_table_rows(obj)
        if rows:
            title_with_metrics = f"{title} (P {obj.sum_metrics.precision:.2f} · R {obj.sum_metrics.recall:.2f} · F{beta} {obj.sum_metrics.f_score(beta):.2f})"
            lines += self._draw_table(["field", "actual", "ground truth", "score", "method"], rows, indent=indent, title=title_with_metrics)
        for k in sorted(obj.properties.keys()):
            v = obj.properties[k]
            if isinstance(v, ComparedObject):
                lines += self._render_object_tables(v, f"{title}.{k}" if title else k, indent + 2, beta)
            elif isinstance(v, ComparedArray):
                lines += self._render_array_table(v, f"{title}.{k}" if title else k, indent + 2, beta)
        return lines

    def _render_array_table(self, arr: ComparedArray, title: str, indent: int, beta: float) -> list[str]:
        headers = ["idx0", "idx1", "field", "actual", "ground truth", "score", "method"]
        rows: list[list[str]] = []
        for i, elem in enumerate(arr.present_items):
            elem_rows = self._collect_rows_from_output(elem.values)
            target = "" if elem.target_index is None else str(elem.target_index)
            if not elem_rows:
                rows.append([str(elem.current_index), target, "*", "", "", "", ""])
            else:
                for j, r in enumerate(elem_rows):
                    idx0 = str(elem.current_index) if j == 0 else ""
                    idx1 = target if j == 0 else ""
                    # If the field starts with this element's own index, strip it to avoid duplication
                    field, actual, expected, score, method = r
                    prefix = f"[{elem.current_index}]"
                    if field.startswith(prefix):
                        field = field[len(prefix) :].lstrip(".")
                    rows.append([idx0, idx1, field, actual, expected, score, method])
            if i < len(arr.present_items) - 1:
                rows.append(["—"] * len(headers))
        # missing items
        for m in arr.missing_items:
            rows.append(["", str(m.target_index), "<missing>", "", str(m.value), "", ""])
        title_with_metrics = f"{title} [] (P {arr.sum_metrics.precision:.2f} · R {arr.sum_metrics.recall:.2f} · F{beta} {arr.sum_metrics.f_score(beta):.2f})"
        return self._draw_table(headers, rows, indent=indent, title=title_with_metrics)

    def report(self, result: CompareResult, beta: float = 1) -> str:
        lines: list[str] = [self._header(result.sum_metrics, beta), ""]
        # Root must be a ComparedObject per model
        root = result.output
        if isinstance(root, ComparedObject):
            lines += self._render_object_tables(root, "Root", indent=0, beta=beta)
        # Fallback: render as single table if not object
        elif isinstance(root, ComparedArray):
            lines += self._render_array_table(root, "Root", indent=0, beta=beta)
        elif isinstance(root, ComparedElement):
            rows = [["$", str(root.test_value), str(root.ground_truth_value), f"{root.score:.2f}", root.method]]
            lines += self._draw_table(["field", "actual", "ground truth", "score", "method"], rows, indent=0, title="Root")
        return "\n".join(lines)
