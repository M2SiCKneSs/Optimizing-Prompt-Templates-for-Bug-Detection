"""
Configuration and data loading for LLM-based Fault Localization.
"""

import os
import re
import glob
import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Set

# =========================
# Paths Configuration
# =========================

BASE_DIR = r"C:\Users\user\Desktop\uni\mark"
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
GROUND_TRUTH_DIR = os.path.join(BASE_DIR, "ground_truth")

BASE_PROMPT_PATTERN = r"^base_prompt_(?P<project>[A-Za-z]+)-(?P<bug_id>\d+)\.txt$"

# Ollama
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"

# Default models (PDF Section 5.6)
DEFAULT_MODELS = ["deepseek-coder:6.7b", "qwen3:8b"]

TEMPLATE_NAMES = {
    1: "trace_aware",
    2: "trace_expected_behavior",
    3: "flexfl_style"
}


# =========================
# Data Classes
# =========================

@dataclass
class ExperimentConfig:
    """Configuration for experiment run."""
    model: str = "deepseek-coder:6.7b"
    template: int = 1
    mode: str = "zero_shot"
    max_iterations: int = 10
    self_consistency_runs: int = 5
    top_k: int = 10
    timeout_seconds: int = 1800
    max_tokens: int = 1024
    temperature_zero_shot: float = 0.2
    temperature_self_consistency: float = 0.7
    save_intermediate: bool = True
    verbose: bool = True


@dataclass(frozen=True)
class PromptReference:
    """Reference to a base prompt file."""
    project: str
    bug_id: int
    path: str


@dataclass
class BugData:
    """Loaded data for a single bug."""
    project: str
    bug_id: int
    raw_content: str
    bug_report: str = ""
    failing_test: str = ""
    failure_trace: str = ""
    code_snippets: str = ""
    test_code_snippet: str = ""


# =========================
# File Operations
# =========================

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def get_output_dir(config: ExperimentConfig, project: str, bug_id: int) -> str:
    template_name = TEMPLATE_NAMES.get(config.template, f"template_{config.template}")
    return os.path.join(
        OUTPUTS_DIR,
        config.model.replace(":", "_"),
        template_name,
        config.mode,
        project,
        f"{project}-{bug_id}"
    )


# =========================
# Data Loading
# =========================

def scan_base_prompts(prompts_dir: Optional[str] = None) -> List[PromptReference]:
    """Scan directory for base prompt files."""
    prompts_dir = prompts_dir or PROMPTS_DIR
    
    if not os.path.isdir(prompts_dir):
        raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")
    
    refs: List[PromptReference] = []
    
    for proj_dir in sorted(glob.glob(os.path.join(prompts_dir, "*"))):
        if not os.path.isdir(proj_dir):
            continue
        
        project = os.path.basename(proj_dir)
        
        for fname in os.listdir(proj_dir):
            match = re.match(BASE_PROMPT_PATTERN, fname)
            if match:
                bug_id = int(match.group("bug_id"))
                refs.append(PromptReference(
                    project=project,
                    bug_id=bug_id,
                    path=os.path.join(proj_dir, fname)
                ))
    
    refs.sort(key=lambda r: (r.project, r.bug_id))
    return refs


def load_bug_data(ref: PromptReference) -> BugData:
    """Load and parse a bug's data from base prompt file."""
    with open(ref.path, "r", encoding="utf-8", errors="ignore") as f:
        raw_content = f.read()
    
    data = BugData(
        project=ref.project,
        bug_id=ref.bug_id,
        raw_content=raw_content
    )
    
    # Parse structured fields
    parsed = _parse_base_prompt(raw_content)
    data.bug_report = parsed.get("bug_report", "")
    data.failing_test = parsed.get("failing_test", "")
    data.failure_trace = parsed.get("failure_trace", "")
    data.code_snippets = parsed.get("code_snippets", "")
    data.test_code_snippet = parsed.get("test_code_snippet", "")
    
    return data


def _parse_base_prompt(content: str) -> Dict[str, str]:
    """Parse base prompt to extract structured fields."""
    result = {
        "bug_report": "",
        "failing_test": "",
        "failure_trace": "",
        "code_snippets": "",
        "test_code_snippet": ""
    }
    
    section_markers = [
        (r"(?:###\s*)?(?:BUG[_\s]?REPORT|Bug\s+Report)\s*:?", "bug_report"),
        (r"(?:###\s*)?(?:FAILING[_\s]?TEST|Failing\s+Test)\s*:?", "failing_test"),
        (r"(?:###\s*)?(?:FAILURE[_\s]?TRACE|Failure\s+Trace|STACK[_\s]?TRACE)\s*:?", "failure_trace"),
        (r"(?:###\s*)?(?:CODE[_\s]?SNIPPETS?|CANDIDATE[_\s]?METHODS?)\s*:?", "code_snippets"),
        (r"(?:###\s*)?(?:TEST[_\s]?CODE[_\s]?SNIPPET)\s*:?", "test_code_snippet"),
    ]
    
    all_patterns = "|".join(f"({p[0]})" for p in section_markers)
    
    sections = []
    for match in re.finditer(all_patterns, content, re.IGNORECASE):
        for i, (pattern, field) in enumerate(section_markers):
            if match.group(i + 1):
                sections.append((match.start(), match.end(), field))
                break
    
    for i, (start, marker_end, field) in enumerate(sections):
        end = sections[i + 1][0] if i + 1 < len(sections) else len(content)
        result[field] = content[marker_end:end].strip()
    
    return result


def load_ground_truth(path: str) -> Dict[str, Dict[int, Set[str]]]:
    """Load ground truth from JSON file."""
    if not os.path.exists(path):
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    result = {}
    for project, bugs in data.items():
        result[project] = {}
        for bug_id, methods in bugs.items():
            result[project][int(bug_id)] = set(methods)
    
    return result


def scan_experiment_outputs(model: str, template: int, mode: str) -> List[tuple]:
    """Scan outputs for completed experiments."""
    template_name = TEMPLATE_NAMES.get(template, f"template_{template}")
    base_path = os.path.join(OUTPUTS_DIR, model.replace(":", "_"), template_name, mode)
    
    if not os.path.isdir(base_path):
        return []
    
    results = []
    
    for project_dir in glob.glob(os.path.join(base_path, "*")):
        if not os.path.isdir(project_dir):
            continue
        
        project = os.path.basename(project_dir)
        
        for bug_dir in glob.glob(os.path.join(project_dir, f"{project}-*")):
            match = re.search(r"-(\d+)$", os.path.basename(bug_dir))
            if not match:
                continue
            
            bug_id = int(match.group(1))
            final_files = sorted(glob.glob(os.path.join(bug_dir, "final_*.json")), reverse=True)
            
            if final_files:
                try:
                    with open(final_files[0], "r", encoding="utf-8") as f:
                        results.append((project, bug_id, json.load(f)))
                except (json.JSONDecodeError, IOError):
                    continue
    
    return results


def get_project_stats(refs: List[PromptReference]) -> Dict[str, int]:
    """Get bug count per project."""
    stats: Dict[str, int] = {}
    for ref in refs:
        stats[ref.project] = stats.get(ref.project, 0) + 1
    return stats
