# JSON Directory

This directory contains the **LLM-generated fault localization rankings** produced by the experiment pipeline. Each JSON file represents the model's ranked list of suspicious methods for a specific bug.

## 📁 Structure

```
json/
├── <Project>/
│   └── <Project>_<bug_id>.json
```

### Projects

**Java (Defects4J):**
- `Math/` - Math_1.json, Math_2.json, ...
- `Lang/` - Lang_1.json, Lang_2.json, ...
- `Chart/` - Chart_1.json, Chart_2.json, ...
- `Time/` - Time_1.json, Time_2.json, ...

**Python (BugsInPy):**
- `black/` - black_1.json, black_2.json, ...
- `thefuck/` - thefuck_1.json, thefuck_2.json, ...
- `tqdm/` - tqdm_1.json, tqdm_2.json, ...

## 📝 File Format

Each JSON file contains:

```json
{
  "project": "<project_name>",
  "bug_id": <integer>,
  "ranking_top5": [
    {
      "rank": 1,
      "method": "<fully_qualified_method_signature>",
      "score": <float>,
      "justification": "<optional reasoning>"
    },
    {
      "rank": 2,
      "method": "<fully_qualified_method_signature>",
      "score": <float>
    },
    ...
  ]
}
```

### Field Descriptions

- **project**: Project name (e.g., "black", "Math", "Lang")
- **bug_id**: Unique bug identifier within the project
- **ranking_top5**: Array of top-5 ranked suspicious methods
  - **rank**: Position in the ranking (1-5)
  - **method**: Method signature in format `project##method_name(params)` or `project$Class#method_name(params)`
  - **score**: Suspiciousness score (0.0-1.0, higher = more suspicious)
  - **justification**: (Optional) LLM's reasoning for the ranking

### Inference Modes

**Zero-Shot Iterative:**
- Runs up to 10 iterations
- Each iteration refines previous ranking
- Final iteration produces the JSON

**Self-Consistency:**
- Runs multiple independent inferences (5-7 times)
- Aggregates results via frequency counting
- Final aggregation produces the JSON

- Method signatures are normalized in `analysis_jsons.py`
- Check normalization logic: `$` → `.`, `##` → `.`, remove whitespace
- Ensure ground truth format matches JSON format
