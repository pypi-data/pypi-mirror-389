# structeval

Structeval is a json comparison cli tool and python library, which supports order-agnostic pairwise matching.

It was built to faciliate evaluation of structured outputs from LLMs, as well as fast comparison of sampled results. Beyond this use case, it also functions as a generic and customizable diffing and matching tool.

## Usage

```bash
uv pip install structeval

structeval --help # To verify install and view cli usage

cat >"left.json" <<'JSON'
{
    "name": "Michael Scott",
    "age": 47,
    "is_athlete": false,
    "metadata": {"date_recorded": "2025-01-01", "location": "Scranton, PA"},
    "hobbies": [
        {"name": "tv", "hours_spent": 10000.0005, "metadata": {"date_started": "2020-01-01"}},
        {"name": "literature", "hours_spent": 0.1, "metadata": {"date_started": "2020-08-01"}},
        {"name": "running", "hours_spent": 90.5, "metadata": {"date_started": "2020-07-01"}}
    ]
}
JSON

cat >"right.json" <<'JSON'
{
    "name": "Michael Scott",
    "age": 47,
    "is_athlete": true,
    "metadata": {"date_recorded": "2025-01-01", "location": "Scranton, PA"},
    "hobbies": [
        {"name": "carbo loading and running", "hours_spent": 90.5, "metadata": {"date_started": "2020-07-01"}},
        {"name": "tv", "hours_spent": 10000, "metadata": {"date_started": "2020-01-01"}},
        {"name": "reading", "hours_spent": 0.1, "metadata": {"date_started": "2020-08-01"}},
        {"name": "comedy", "hours_spent": 1000000, "metadata": {"date_started": "1970-08-01"}}
    ]
}
JSON

# Structured json report to stdout
structeval --test "left.json" --gt "right.json" --report json

# Text report to stdout
structeval --test "left.json" --gt "right.json" --report text

# This will open a report in the browser
structeval --test "left.json" --gt "right.json" --report html > report.html && open report.html

```
#### Text report visual
![Example text report](examples/screenshots/basic.png)

## Customization

```bash
# You can customize comparison logic in a config file
# Here we specify embeddings for string fields by default
cat >"config.json" <<'JSON'
{
    "string_evaluation_type": {
        "evaluation_type": "cosine",
        "evaluation_params": {
            "embedding_model": "all-MiniLM-L6-v2"
        }
    },
    "number_evaluation_type": {
        "evaluation_type": "threshold",
        "evaluation_params": {
            "threshold": 10,
            "difference_penalty_weighting": 1
        }
    },
    "array_matching_threshold": 0.4
}
JSON

structeval --test "left.json" --gt "right.json" --config config.json --report text
```

#### Configuration options

| Option | Type | Default | Description | Supported evaluation_type | evaluation_params |
|---|---|---|---|---|---|
| `string_evaluation_type` | object | Jaccard | Evaluator used for string fields. By default compares token sets with Jaccard similarity. | `jaccard`, `cosine`, `binary` | For `cosine`: `{ "embedding_model": "all-MiniLM-L6-v2" }` |
| `boolean_evaluation_type` | object | Binary | Evaluator for boolean fields. Exact match by default. | `binary` | — |
| `integer_evaluation_type` | object | Binary | Evaluator for integer fields. Exact match by default. | `binary`, `threshold` | For `threshold`: `{ "threshold": <float>, "difference_penalty_weighting": <float≥0> }` |
| `float_evaluation_type` | object | Threshold(0.001, 0.1) | Evaluator for float fields. Scores 1.0 within threshold; otherwise decays with penalty weighting. | `threshold`, `binary` | `{ "threshold": <float>, "difference_penalty_weighting": <float≥0> }` |
| `array_matching_threshold` | number | 0.3 | Minimum similarity required for pairing elements across arrays. Lower values allow looser matches; higher values require stronger matches. | — | — |

Notes
- Cosine evaluator uses sentence-transformer embeddings; set `embedding_model` to any supported name (e.g., `all-MiniLM-L6-v2`).

#### Text report visual (with config applied)
![Example text report](examples/screenshots/basic.png)


## JSON Schema

For the most part, any two valid jsons of any shape can be compared and will return sensible comparison metrics and details -- this enables the `structeval` cli to function as a generic json diffing tool if so desired.

However, it is probably most common to compare with a schema in mind. To this end, providing a schema can help further refine the validation by allowing for more type awareness. When specifying a schema, the following logic is applied:
1. all properties not listed in schema are ignored (but `additionalProperties == true` or you'll get an error messsage)
2. retrieving field-level evaluators or comparers
3. more type customization: enums are defaulted to binary comparison (possibly more could be done here)

You can set per-field rules in your schema via the
`x-override-evaluator` key:

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "x-override-evaluator": {"evaluation_type": "binary"}
    }
  }
}
```

## Configuration (by type)

```python
from structeval.models.eval_config import (
    EvalConfig, EvaluationDefinition, EvaluationType
)
from structeval import StructEvaluator

# Example: make string comparisons binary by default; keep other types default
cfg = EvalConfig(
    string_evaluation_type=EvaluationDefinition(
        evaluation_type=EvaluationType.BINARY
    )
    # optionally: boolean_evaluation_type, integer_evaluation_type,
    # float_evaluation_type, and array_matching_threshold (float)
)

result = StructEvaluator.run(left, right, configuration=cfg)
print(result.precision, result.recall, result.f_score())

# You can also pass the same JSON (dict) as --config to the CLI
```

## Library quick start (full control)

```python
from structeval import StructEvaluator
from structeval.models.compare_result import CompareResult

left = {"name": "John", "age": 25, "is_student": True,
         "hobbies": [{"name": "reading"}, {"name": "swimming"}]}
right = {"name": "Jane", "age": 26, "is_student": True,
          "hobbies": [{"name": "hiking"}, {"name": "swimming"}, {"name": "buildings"}]}

# Compare arbitrary JSON – nested objects and arrays supported
result: CompareResult = StructEvaluator.run(left, right)
metrics = result.sum_metrics
print(metrics.precision, metrics.recall, metrics.f_score())
print(result.output) # This produces metrics and details recursively about each comparison -- the data used to produce the reports. See code for more details. 

# You can also pass in pydantic models through the run_typed method
result: CompareResult = StructEvaluator.run_typed(left_mode, right_model)
```

### BYO Evaluator

```python
from Levenshtein import ratio as levenshtein_ratio

from structeval.compare.methods.scalar.typed_evaluator import TypedEvaluator 
from structeval.models.evaluators import Evaluators
from structeval.struct_evaluator import StructEvaluator


class LevenshteinStringEvaluator(TypedEvaluator):
    """Levenshtein similarity for strings using python-Levenshtein's ratio (0..1)."""

    def __call__(self, value0, value1) -> float:
        return float(levenshtein_ratio(s0, s1))

    def name(self) -> str:
        return "LevenshteinRatio"

# Wire it in
evaluators = Evaluators.default()
evaluators.string_compare = LevenshteinStringEvaluator()

left = {"name": "John Jingleheimer"}
right = {"name": "Jhon Jingleheimer"}
result = StructEvaluator.run(left, right, evaluators=evaluators)
print(result) 
```

### Reporting (text)

```python
from structeval.reporting.text import TextReporter

print(TextReporter(use_color=True).report(comparison_output))
```

### Reporting (HTML)

```python
from structeval.reporting.html import HtmlReporter

html = HtmlReporter().report(comparison_output)
with open("report.html", "w", encoding="utf-8") as f:
    f.write(html)

```

### Evaluators provided

| Evaluator | Type | Default for | Purpose/behavior | Key params |
|---|---|---|---|---|
| Binary | scalar | booleans, integers | Exact equality: 1.0 if values are equal, else 0.0 | — |
| Threshold | scalar | floats (default config) | Scores 1.0 when absolute difference ≤ threshold; otherwise decreases toward 0 based on penalty. See formula in code. | `threshold` (float, > 0), `difference_penalty_weighting` (float, ≥ 0; 0=no penalty, 1=linear, 2=quadratic, …) |
| Jaccard | vector (wrapped for scalar strings) | strings (via wrapper) | Tokenizes strings (lowercase, whitespace split), computes Jaccard similarity of token sets. Used for both scalar and array matching of strings. | `tokenizer` (callable, optional; defaults to simple whitespace tokenizer) |
| Cosine | vector | — | Embedding-based cosine similarity between strings for semantic comparison. Only sentence-transfomer models are supported now. | `embedding_model` (str; e.g. `all-MiniLM-L6-v2`) |


### Notes and caveats on metrics

- Scores are determined based on the evaluator. While they are all normalized 0-1, they are not perfectly calibrated, so results from different json shapes and evaluator mixes are only ~roughly comparable.
- All scalar attributes present within the json payload are weighted equally. 
- In order to calculate precision and recall, the following formulas are applied: `sum(gt_example_attributes) == True Positives + False Negatives`, `sum(test_attributes) == True Positives + False Positives`. `sum(all_scalar_scores_when_matched) == True Positives`.
- Metrics are calculated recursively and available for each nested non-scalar type. 

## Getting started with development

```
gh repo clone jhiker/structeval && cd structeval
make venv # activate env
make install
make test # (includes property-based tests using hypothesis, which can take a second the first time)
```