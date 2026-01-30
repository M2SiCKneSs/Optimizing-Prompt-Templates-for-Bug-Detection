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

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) (for local LLM serving)
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/M2SiCKneSs/Optimizing-Prompt-Templates-for-Bug-Detection.git
   cd Optimizing-Prompt-Templates-for-Bug-Detection
   ```

2. **Install dependencies**
   ```bash
   pip install requests
   ```

3. **Install and setup Ollama**
   ```bash
   # Install Ollama from https://ollama.ai/
   
   # Pull required models
   ollama pull qwen3:8b
   ollama pull deepseek-coder:6.7b
   ```

4. **Verify Ollama is running**
   ```bash
   ollama ps
   ollama list
   ```

5. **Configure paths**
   
   Edit `code/Experiment_code/config.py` to set your data directory:
   ```python
   BASE_DIR = r"C:\path\to\your\data"
   ```

## 🚀 Quick Start

### Option 1: Using the Modular CLI (Recommended)

```bash
cd code/Experiment_code

# Run experiment with Template 1 (Trace-aware)
python main.py run --model deepseek-coder:6.7b --template 1 --mode zero_shot

# Run experiment with Template 2 (Trace + Expected Behavior)
python main.py run --model qwen3:8b --template 2 --mode self_consistency

# Evaluate results
python main.py evaluate --model deepseek-coder:6.7b --template 1 --mode zero_shot \
    --ground-truth ../../Ground_truth/ground_truth.json --benchmark python -o results.txt
```

### Option 2: Build Base Prompts First

If you need to generate base prompts from raw data:

```bash
cd code

# Run complete pipeline (3 steps)
python base_propmt_pipeline.py

# Or run each step manually:
python build_all_base_prompts_bug_report.py
python enrich_base_prompts_with_tests_and_snippets.py --top_n 10
python append_failure_trace_to_all_base_prompts.py
```

## 📖 Detailed Usage

### Experiment Pipeline Architecture

The modular pipeline consists of five core components:

| File | Description |
|------|-------------|
| **main.py** | CLI with `run`, `evaluate`, and `list` commands |
| **config.py** | Paths, settings, data classes, and file operations |
| **prompts.py** | Template 1, 2, 3 implementations (PDF Section 4.3) |
| **engine.py** | Ollama client, zero-shot/self-consistency inference (Algorithm 1) |
| **evaluation.py** | Top-K hits, precision, recall, F1, accuracy computation |

### Running Experiments

#### Command Structure

```bash
python main.py run --model <MODEL> --template <1|2|3> --mode <zero_shot|self_consistency> [OPTIONS]
```

#### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--model` | str | required | Ollama model (e.g., `qwen3:8b`, `deepseek-coder:6.7b`) |
| `--template` | int | required | 1=Trace-aware, 2=Trace+Expected, 3=FlexFL-style |
| `--mode` | str | required | `zero_shot` or `self_consistency` |
| `--max-iters` | int | 10 | Max iterations for zero-shot (convergence limit) |
| `--runs` | int | 5 | Number of runs for self-consistency |
| `--top-k` | int | 10 | Number of methods to rank |
| `--timeout` | int | 1800 | Timeout per LLM request (seconds) |
| `--max-tokens` | int | 1024 | Maximum tokens to generate |
| `--temp-zero` | float | 0.2 | Temperature for zero-shot mode |
| `--temp-sc` | float | 0.7 | Temperature for self-consistency |
| `--project` | list | all | Filter by project(s), e.g., `--project black thefuck` |
| `--bug-id` | list | all | Filter by bug ID(s), e.g., `--bug-id 1 2 3` |

#### Examples

**Template 1 (Trace-aware) with Zero-shot:**
```bash
python main.py run --model deepseek-coder:6.7b --template 1 --mode zero_shot
```

**Template 2 (Trace + Expected Behavior) with Self-consistency:**
```bash
python main.py run --model qwen3:8b --template 2 --mode self_consistency --runs 7
```

**Template 3 (FlexFL baseline):**
```bash
python main.py run --model deepseek-coder:6.7b --template 3 --mode zero_shot
```

**Filter specific projects and bugs:**
```bash
python main.py run --model qwen3:8b --template 1 --mode zero_shot \
    --project black thefuck --bug-id 1 2 3
```

### Evaluating Results

#### Command Structure

```bash
python main.py evaluate --model <MODEL> --template <1|2|3> --mode <MODE> \
    --ground-truth <PATH> --benchmark <python|java> [OPTIONS]
```

#### Ground Truth Format

Create `ground_truth.json`:

```json
{
  "black": {
    "1": ["black.main", "black.format_file"],
    "2": ["black.decode_bytes"]
  },
  "thefuck": {
    "1": ["thefuck.corrector.fix_command"]
  }
}
```

Or use existing text files (converted automatically):
```
1 : tqdm.contrib.__init__##tenumerate(iterable,start,total,tqdm_class,**tqdm_kwargs)
2 : tqdm.std$tqdm#print_status(s)
```

#### Evaluation Examples

**Python (BugsInPy) format:**
```bash
python main.py evaluate --model deepseek-coder:6.7b --template 1 --mode zero_shot \
    --ground-truth ground_truth.json --benchmark python -o python_results.txt
```

**Java (Defects4J) format:**
```bash
python main.py evaluate --model qwen3:8b --template 2 --mode self_consistency \
    --ground-truth ground_truth.json --benchmark java -o java_results.txt
```

### Listing Available Data

```bash
# List all available base prompts
python main.py list prompts

# List completed experiment runs
python main.py list experiments
```

### Output Structure

Experiments generate organized outputs:

```
outputs/
└── <model_name>/
    └── <template_name>/
        └── <mode>/
            └── <Project>/
                └── <Project>-<bug_id>/
                    ├── iter_01_raw.txt           # Zero-shot iteration outputs
                    ├── iter_02_raw.txt
                    ├── ...
                    ├── run_01_raw.txt            # Self-consistency run outputs
                    ├── run_02_raw.txt
                    ├── ...
                    ├── final_<timestamp>.json    # Final ranking
                    └── expected_behavior_<timestamp>.txt  # Template 2 only
```

## 🔬 Methodology

### Prompt Templates (PDF Section 4.3)

| Template | Name | Description |
|----------|------|-------------|
| **1** | Trace-aware | Uses failure trace to rank suspicious methods based on execution evidence |
| **2** | Trace + Expected Behavior | Extracts expected behavior from test, compares with observed failure |
| **3** | FlexFL-style | Agent-style baseline inspired by FlexFL's localization refinement |

### Inference Strategies (PDF Section 4.3.1)

| Mode | Description | Key Features |
|------|-------------|--------------|
| **zero_shot** | Iterative refinement | • Max 10 iterations<br>• Converges when ranking stabilizes<br>• Temperature: 0.2 |
| **self_consistency** | Independent multi-run aggregation | • 5-7 independent runs<br>• Aggregated by frequency + avg rank<br>• Temperature: 0.7 |

### Algorithmic Workflow (Algorithm 1)

```
1. Initialize diagnosis list L₀
2. For i = 0 to max_iterations:
   a. Construct prompt with current list Lᵢ
   b. Query LLM → Response
   c. Parse and rank → Lᵢ₊₁
   d. If Lᵢ₊₁ == Lᵢ: break (converged)
3. Return final list
```

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

| Project | Precision | Recall | F1-Score | Accuracy |
|---------|-----------|--------|----------|----------|
| Time | 0.1750 | 0.4865 | 0.2265 | 0.9882 |
| Math | 0.2488 | 0.7128 | 0.3392 | 0.9588 |
| Lang | 0.2882 | 0.6554 | 0.3243 | 0.9003 |
| Chart | 0.2500 | 0.5699 | 0.3026 | 0.9005 |

**Python Projects:**

| Project | Precision | Recall | F1-Score | Accuracy |
|---------|-----------|--------|----------|----------|
| black | 0.0143 | 0.0714 | 0.0238 | 0.9597 |
| thefuck | 0.1667 | 0.0936 | 0.0468 | 0.8168 |
| tqdm | 0.0571 | 0.2857 | 0.0952 | 0.9376 |

### Statistical Significance (Wilcoxon Signed-Rank Test, α=0.05)

| Comparison | Dataset | p-value | Significant? |
|------------|---------|---------|--------------|
| Template 2 vs. FlexFL | Java | 0.0124 | ✅ Yes |
| Template 2 vs. Template 1 | Java | 0.0310 | ✅ Yes |
| Self-Cons. vs. Zero-Shot | Overall | 0.0421 | ✅ Yes |
| Template 2 vs. FlexFL | Python | 0.0845 | ❌ No |

## 🔧 Troubleshooting

### Common Issues

**1. Ollama Connection Errors**
```bash
# Ensure Ollama is running
ollama ps

# Restart Ollama
# Windows: Restart from system tray
# Linux/Mac: killall ollama && ollama serve
```

**2. Timeout Errors**
```bash
# Increase timeout and reduce token limit
python main.py run --model qwen3:8b --template 1 --mode zero_shot \
    --timeout 3600 --max-tokens 600
```

**3. Model Not Found**
```bash
# Pull the required model
ollama pull qwen3:8b
ollama pull deepseek-coder:6.7b

# List available models
ollama list
```

**4. Ground Truth Format Errors**
- Ensure JSON is valid: `python -m json.tool ground_truth.json`
- Check bug IDs match between ground truth and prompts
- Verify method signatures are normalized

**5. No Prompts Found**
```bash
# Check BASE_DIR in config.py points to correct location
# Run the base prompt pipeline first:
cd code
python base_propmt_pipeline.py
```

## 📚 Documentation

Each major directory contains detailed documentation:

- **[code/Experiment_code/README.md](code/Experiment_code/README.md)** - Detailed pipeline usage
- **[prompts/README.md](prompts/README.md)** - Prompt file format and generation
- **[json/README.md](json/README.md)** - LLM output format
- **[Ground_truth/README.md](Ground_truth/README.md)** - Ground truth specifications
- **[Res/README.md](Res/README.md)** - Results interpretation

## 🔬 Reproducing Paper Results

To reproduce the exact results from our paper:

```bash
# 1. Ensure base prompts exist
cd code
python base_propmt_pipeline.py

# 2. Run all configurations
cd Experiment_code

# Java experiments with Qwen3:8B
python main.py run --model qwen3:8b --template 1 --mode zero_shot --max-iters 10
python main.py run --model qwen3:8b --template 1 --mode self_consistency --runs 7
python main.py run --model qwen3:8b --template 2 --mode zero_shot --max-iters 10
python main.py run --model qwen3:8b --template 2 --mode self_consistency --runs 7

# Java experiments with DeepSeek:6.7B
python main.py run --model deepseek-coder:6.7b --template 1 --mode zero_shot
python main.py run --model deepseek-coder:6.7b --template 2 --mode self_consistency

# 3. Evaluate all results
python main.py evaluate --model qwen3:8b --template 2 --mode self_consistency \
    --ground-truth ../../Ground_truth/ground_truth.json \
    --benchmark python -o ../../Res/python/python_results.txt
```

## 📄 Citation

If you use this code or data in your research, please cite our paper:

```bibtex
@inproceedings{goldfarb2025optimizing,
  title={Optimizing Prompt Templates for Bug Detection},
  author={Goldfarb, Michael and Lisiansky, Maxim and Kremer, Roy and Paz, Osher},
  booktitle={Research Methods in Information Systems},
  year={2025},
  institution={Ben-Gurion University of the Negev}
}
```

## 👥 Authors

- **Michael Goldfarb** - goldfmic@post.bgu.ac.il
- **Maxim Lisiansky** - maximlis@post.bgu.ac.il
- **Roy Kremer** - roykr@post.bgu.ac.il
- **Osher Paz** - osherp@post.bgu.ac.il

*Ben-Gurion University of the Negev, Beer-Sheva, Israel*

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Defects4J team for the Java bug benchmark
- BugsInPy team for the Python bug benchmark
- Ollama for local LLM serving infrastructure
- FlexFL authors for baseline inspiration

---

**Note:** This is research code. While we've made every effort to ensure reproducibility, exact results may vary slightly due to LLM non-determinism and hardware differences.
