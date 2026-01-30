# LLM Fault Localization Pipeline

Implements "Optimizing Prompt Templates for Bug Detection - Team 19"

## Files

| File | Description |
|------|-------------|
| `main.py` | CLI commands (run, evaluate, list) |
| `config.py` | Paths, settings, data loading |
| `prompts.py` | Templates 1, 2, 3 from PDF |
| `engine.py` | Ollama client, inference (zero-shot/self-consistency) |
| `evaluation.py` | Metrics computation, report generation |

## Setup

```bash
pip install requests

# Pull Ollama models
ollama pull deepseek-coder:6.7b
ollama pull qwen3:8b
```

Edit `config.py` to set your paths:
```python
BASE_DIR = r"C:\Users\user\Desktop\uni\mark"
```

## Commands

### Run Experiment

```bash
# Template 1: Trace-aware
python main.py run --model deepseek-coder:6.7b --template 1 --mode zero_shot

# Template 2: Trace + Expected Behavior  
python main.py run --model deepseek-coder:6.7b --template 2 --mode self_consistency

# Template 3: FlexFL baseline
python main.py run --model deepseek-coder:6.7b --template 3 --mode zero_shot

# Filter by project/bug
python main.py run --model deepseek-coder:6.7b --template 1 --mode zero_shot \
    --project Black --bug-id 1 2 3
```

### Evaluate Results

```bash
# Python format (BugsInPy)
python main.py evaluate --model deepseek-coder:6.7b --template 1 --mode zero_shot \
    --ground-truth ground_truth.json --benchmark python -o python_res.txt

# Java format (Defects4J)
python main.py evaluate --model deepseek-coder:6.7b --template 1 --mode zero_shot \
    --ground-truth ground_truth.json --benchmark java -o java_res.txt
```

### List Data

```bash
python main.py list prompts      # Available bugs
python main.py list experiments  # Completed runs
```

## Ground Truth

Create `ground_truth.json`:
```json
{
  "black": {
    "1": ["buggy_method"],
    "2": ["method1", "method2"]
  },
  "thefuck": {
    "1": ["fix_command"]
  }
}
```

## Output Format

**Python (BugsInPy):**
```
BugsInPy Classification Metrics (K=5)
==================================================

Project: black (14 bugs analyzed)
  Top-1 Hits: 0
  Top-3 Hits: 0
  Top-5 Hits: 1
  Mean Precision: 0.0143
  Mean Recall:    0.0714
  Mean F1 Score:  0.0238
  Mean Accuracy:  0.9597

GLOBAL AVERAGES
---------------
Total Bugs Processed: 33
Average F1 Score:     0.0473
Average Accuracy:     0.9030
```

**Java (Defects4J):**
```
Fault Localization Evaluation (K=5)
========================================

Project: Math (41 bugs)
  Top-1 Hits: 20
  Top-3 Hits: 31
  Top-5 Hits: 35
  Mean Precision: 0.2488
  Mean Recall:    0.7128
  Mean F1:        0.3392
  Mean Accuracy:  0.9588

OVERALL TOTALS
---------------
Total Bugs Analyzed: 121
Total Top-1: 62
Total Top-3: 88
Total Top-5: 99
Average Precision: 0.2455
Average Recall:    0.6258
Average F1:        0.3060
Average Accuracy:  0.9376
```

## Templates (PDF Section 4.3)

| # | Name | Description |
|---|------|-------------|
| 1 | Trace-aware | Uses failure trace to rank suspicious methods |
| 2 | Trace + Expected | Extracts expected behavior, compares with observed |
| 3 | FlexFL-style | Baseline agent prompt from FlexFL paper |

## Modes (PDF Section 4.3.1)

| Mode | Description |
|------|-------------|
| `zero_shot` | Iterative refinement, max 10 iterations, converges when stable |
| `self_consistency` | 5 independent runs, aggregated by frequency + avg rank |
