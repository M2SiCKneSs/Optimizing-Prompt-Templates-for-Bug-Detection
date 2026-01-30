# Optimizing Prompt Templates for Bug Detection

This repository contains the implementation and experimental artifacts for our Research Methods in Information Systems paper: **"Optimizing Prompt Templates for Bug Detection"** by Michael Goldfarb, Maxim Lisiansky, Roy Kremer, and Osher Paz from Ben-Gurion University of the Negev.

## 📋 Table of Contents

- [Overview](#overview)
- [Key Contributions](#key-contributions)
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
- [Methodology](#methodology)
- [Results](#results)
- [Citation](#citation)

## 🔍 Overview

This research explores train-free, LLM-based fault localization using locally served open-source models (Qwen3:8B and DeepSeek-Coder:6.7B). We propose an iterative methodology that integrates dynamic artifacts such as failing test traces and natural-language "expected behavior" summaries into structured prompts, evaluated across **Defects4J** (Java) and **BugsInPy** (Python) benchmarks.

### Research Questions

- **RQ1**: Does changing the prompt template or inference category (Zero-shot vs. Self-consistency) significantly affect performance?
- **RQ2**: Does the choice of the underlying LLM significantly affect localization accuracy?
- **RQ3**: Can our proposed templates yield better performance than established agent-style baselines?

## 🎯 Key Contributions

1. **Controlled experimental framework** for evaluating prompt templates in LLM-based fault localization
2. **Unified prompt input representation** enabling fair comparison across diverse templates and models
3. **Systematic comparison** between zero-shot, self-consistency, and trace-aware prompting strategies
4. **Offline, lightweight, reproducible** evaluation setup using locally served open-source LLMs

## 📁 Repository Structure

```
.
├── code/
│   ├── Experiment_code/           # Modular experiment pipeline
│   │   ├── main.py                # CLI interface (run/evaluate/list)
│   │   ├── config.py              # Configuration and data loading
│   │   ├── prompts.py             # Template definitions (1, 2, 3)
│   │   ├── engine.py              # LLM client and inference strategies
│   │   └── evaluation.py          # Metrics computation and reporting
│   │
│   ├── build_all_base_prompts_bug_report.py
│   ├── enrich_base_prompts_with_tests_and_snippets.py
│   ├── append_failure_trace_to_all_base_prompts.py
│   ├── base_propmt_pipeline.py    # Wrapper to run pipeline in order
│   └── analysis_jsons.py          # Legacy metrics analyzer
│
├── prompts/                       # Generated base prompts
│   ├── black/, thefuck/, tqdm/    # Python projects
│   └── Math/, Lang/, Chart/, Time/ # Java projects
│
├── json/                          # LLM-generated rankings
├── Ground_truth/                  # Ground truth buggy methods
├── FAILURE_TRACE/                 # Stack traces from failing tests
├── FAILING_TEST/                  # Lists of failing test methods
├── CODE_SNIPPETS/                 # Source code snippets
├── BUG_REPORT/                    # Bug report JSON files
└── Res/                           # Experimental results
    ├── java/
    └── python/
```

The modular pipeline consists of five core components:

| File | Description |
|------|-------------|
| **main.py** | CLI with `run`, `evaluate`, and `list` commands |
| **config.py** | Paths, settings, data classes, and file operations |
| **prompts.py** | Template 1, 2, 3 implementations (PDF Section 4.3) |
| **engine.py** | Ollama client, zero-shot/self-consistency inference (Algorithm 1) |
| **evaluation.py** | Top-K hits, precision, recall, F1, accuracy computation |


## 🔬 Methodology

### Prompt Templates (PDF Section 4.3)

| Template | Name | Description |
|----------|------|-------------|
| **1** | Trace-aware | Uses failure trace to rank suspicious methods based on execution evidence |
| **2** | Trace + Expected Behavior | Extracts expected behavior from test, compares with observed failure |
| **3** | FlexFL-style | Agent-style baseline inspired by FlexFL's localization refinement |



## 📊 Results

### Java (Defects4J) - 121 Bugs Analyzed

| Configuration | Top-1 | Top-3 | Top-5 |
|---------------|-------|-------|-------|
| **Qwen3:8B** |
| Template 1 + Zero-shot | 14.7% | 23.3% | 29.3% |
| Template 1 + Self-cons. | 17.0% | 25.9% | 30.8% |
| Template 2 + Zero-shot | 17.2% | 26.8% | 29.8% |
| Template 2 + Self-cons. | **17.3%** | **26.9%** | **32.2%** |
| FlexFL Baseline (T3) | 13.2% | 19.0% | 23.0% |
| **DeepSeek-Coder:6.7B** |
| Template 1 + Zero-shot | 13.7% | 26.0% | 28.3% |
| Template 2 + Self-cons. | 15.0% | 25.5% | 29.8% |

### Python (BugsInPy) - 33 Bugs Analyzed

| Configuration | Top-1 | Top-3 | Top-5 |
|---------------|-------|-------|-------|
| **Qwen3:8B** |
| Template 2 + Self-cons. | 4.7% | 7.7% | 8.9% |
| **DeepSeek-Coder:6.7B** |
| Template 1 + Self-cons. | **6.6%** | 6.8% | 11.6% |

### Classification Metrics (K=5)

**Java Projects:**

| Project | Precision | Recall | F1-Score | 
|---------|-----------|--------|----------|
| Time | 0.1750 | 0.4865 | 0.2265 | 
| Math | 0.2488 | 0.7128 | 0.3392 | 
| Lang | 0.2882 | 0.6554 | 0.3243 | 
| Chart | 0.2500 | 0.5699 | 0.3026 |

**Python Projects:**

| Project | Precision | Recall | F1-Score |
|---------|-----------|--------|----------|
| black | 0.0143 | 0.0714 | 0.0238 |
| thefuck | 0.1667 | 0.0936 | 0.0468 |
| tqdm | 0.0571 | 0.2857 | 0.0952 |

### Statistical Significance (Wilcoxon Signed-Rank Test, α=0.05)

| Comparison | Dataset | p-value | Significant? |
|------------|---------|---------|--------------|
| Template 2 vs. FlexFL | Java | 0.0124 | ✅ Yes |
| Template 2 vs. Template 1 | Java | 0.0310 | ✅ Yes |
| Self-Cons. vs. Zero-Shot | Overall | 0.0421 | ✅ Yes |
| Template 2 vs. FlexFL | Python | 0.0845 | ❌ No |



## 📚 Documentation

Each major directory contains detailed documentation:

- **[code/Experiment_code/README.md](code/Experiment_code/README.md)** - Detailed pipeline usage
- **[prompts/README.md](prompts/README.md)** - Prompt file format and generation
- **[json/README.md](json/README.md)** - LLM output format
- **[Ground_truth/README.md](Ground_truth/README.md)** - Ground truth specifications
- **[Res/README.md](Res/README.md)** - Results interpretation


## 📄 Citation

If you use this code or data in your research, please cite our paper:

```bibtex
@inproceedings{2026optimizing,
  title={Optimizing Prompt Templates for Bug Detection},
  author={Goldfarb, Michael and Lisiansky, Maxim and Kremer, Roy and Paz, Osher},
  booktitle={Research Methods in Information Systems},
  year={2026},
  institution={Ben-Gurion University of the Negev}
}
```

## 👥 Authors

- **Michael Goldfarb** - goldfmic@post.bgu.ac.il
- **Maxim Lisiansky** - maximlis@post.bgu.ac.il
- **Roy Kremer** - roykr@post.bgu.ac.il
- **Osher Paz** - osherp@post.bgu.ac.il

*Ben-Gurion University of the Negev, Beer-Sheva, Israel*


## 🙏 Tools & Repos

- Defects4J - https://github.com/rjust/defects4j
- BugsInPy - https://github.com/soarsmu/BugsInPy
- Ollama - https://docs.ollama.com/
- Gzoltar - https://gzoltar.com/
- FlexFL- https://dl.acm.org/doi/10.1109/TSE.2025.3553363

---

**Note:** This is research code. While we've made every effort to ensure reproducibility, exact results may vary slightly due to LLM non-determinism and hardware differences.
