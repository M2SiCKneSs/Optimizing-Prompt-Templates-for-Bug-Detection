"""
Engine module: LLM client and inference strategies.
Implements Algorithm 1 from PDF Section 4.4.
"""

import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import requests

from config import OLLAMA_GENERATE_URL, OLLAMA_BASE_URL, ensure_dir
from prompts import PromptBuilder


# =========================
# Data Classes
# =========================

@dataclass
class LLMResponse:
    raw_text: str
    parsed_json: Optional[Dict]
    error: Optional[str] = None
    latency_seconds: float = 0.0


@dataclass
class InferenceResult:
    final_ranking: List[Dict[str, str]]
    iterations_used: int
    converged: bool
    all_iterations: List[Dict] = field(default_factory=list)
    expected_behavior: Optional[List[str]] = None
    errors: List[str] = field(default_factory=list)
    total_latency_seconds: float = 0.0


# =========================
# Ollama Client
# =========================

class OllamaClient:
    """Client for Ollama API."""
    
    def __init__(self, model: str, timeout_seconds: int = 1800, 
                 max_tokens: int = 1024, temperature: float = 0.2):
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    def is_available(self) -> bool:
        try:
            r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            return r.status_code == 200
        except:
            return False
    
    def generate(self, prompt: str, temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None) -> LLMResponse:
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": tokens, "temperature": temp}
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(OLLAMA_GENERATE_URL, json=payload, 
                                    timeout=self.timeout_seconds)
            response.raise_for_status()
            
            raw_text = response.json().get("response", "")
            parsed_json, error = self._extract_json(raw_text)
            
            return LLMResponse(
                raw_text=raw_text,
                parsed_json=parsed_json,
                error=error,
                latency_seconds=time.time() - start_time
            )
        except Exception as e:
            return LLMResponse(
                raw_text="",
                parsed_json=None,
                error=str(e),
                latency_seconds=time.time() - start_time
            )
    
    def _extract_json(self, text: str) -> tuple:
        if not text.strip():
            return None, "Empty response"
        
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        start = text.find("{")
        end = text.rfind("}")
        
        if start == -1 or end == -1 or end <= start:
            return None, "No JSON found"
        
        try:
            parsed = json.loads(text[start:end + 1])
            return parsed, None
        except json.JSONDecodeError as e:
            return None, f"JSON parse error: {e}"


# =========================
# Helper Functions
# =========================

def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def extract_top_k_methods(response: LLMResponse) -> List[Dict[str, str]]:
    if response.parsed_json is None:
        return []
    
    top_k = response.parsed_json.get("top_k", [])
    if not isinstance(top_k, list):
        return []
    
    results = []
    for item in top_k:
        if isinstance(item, dict):
            method = item.get("method", "") or item.get("method_name", "")
            if method:
                results.append({
                    "method": str(method).strip(),
                    "justification": str(item.get("justification", "")).strip()
                })
    return results


def methods_to_json(methods: List[Dict[str, str]]) -> str:
    return json.dumps([{"method": m["method"]} for m in methods], ensure_ascii=False)


# =========================
# Inference Strategies
# =========================

def run_zero_shot_iterative(
    client: OllamaClient,
    prompt_builder: PromptBuilder,
    base_prompt: str,
    output_dir: str,
    max_iterations: int = 10,
    temperature: float = 0.2,
    save_intermediate: bool = True,
    verbose: bool = True
) -> InferenceResult:
    """Zero-shot iterative inference (Algorithm 1)."""
    ensure_dir(output_dir)
    
    prev_candidates = "[]"
    prev_methods: Optional[List[str]] = None
    all_iterations = []
    total_latency = 0.0
    errors = []
    
    for iteration in range(1, max_iterations + 1):
        if verbose:
            print(f"  Iteration {iteration}/{max_iterations}...", end=" ", flush=True)
        
        full_prompt = prompt_builder.wrap_zero_shot(base_prompt, prev_candidates)
        response = client.generate(prompt=full_prompt, temperature=temperature)
        total_latency += response.latency_seconds
        
        if save_intermediate:
            with open(os.path.join(output_dir, f"iter_{iteration:02d}_raw.txt"), "w", encoding="utf-8") as f:
                f.write(response.raw_text)
        
        if response.error and response.parsed_json is None:
            errors.append(f"Iteration {iteration}: {response.error}")
            if verbose:
                print(f"ERROR")
            continue
        
        methods = extract_top_k_methods(response)
        method_names = [m["method"] for m in methods]
        
        all_iterations.append({
            "iteration": iteration,
            "methods": methods,
            "latency_seconds": response.latency_seconds
        })
        
        if verbose:
            print(f"{len(methods)} methods")
        
        # Check convergence
        if prev_methods is not None and method_names == prev_methods:
            if verbose:
                print(f"  Converged at iteration {iteration}")
            result = InferenceResult(
                final_ranking=methods, iterations_used=iteration,
                converged=True, all_iterations=all_iterations,
                errors=errors, total_latency_seconds=total_latency
            )
            _save_result(result, output_dir)
            return result
        
        prev_methods = method_names
        prev_candidates = methods_to_json(methods)
    
    final_methods = all_iterations[-1]["methods"] if all_iterations else []
    result = InferenceResult(
        final_ranking=final_methods, iterations_used=max_iterations,
        converged=False, all_iterations=all_iterations,
        errors=errors, total_latency_seconds=total_latency
    )
    _save_result(result, output_dir)
    return result


def run_self_consistency(
    client: OllamaClient,
    prompt_builder: PromptBuilder,
    base_prompt: str,
    output_dir: str,
    num_runs: int = 5,
    temperature: float = 0.7,
    top_k: int = 10,
    save_intermediate: bool = True,
    verbose: bool = True
) -> InferenceResult:
    """Self-consistency inference with aggregation."""
    ensure_dir(output_dir)
    
    all_runs = []
    total_latency = 0.0
    errors = []
    
    for run_idx in range(1, num_runs + 1):
        if verbose:
            print(f"  Run {run_idx}/{num_runs}...", end=" ", flush=True)
        
        full_prompt = prompt_builder.wrap_self_consistency(base_prompt)
        response = client.generate(prompt=full_prompt, temperature=temperature)
        total_latency += response.latency_seconds
        
        if save_intermediate:
            with open(os.path.join(output_dir, f"run_{run_idx:02d}_raw.txt"), "w", encoding="utf-8") as f:
                f.write(response.raw_text)
        
        if response.error and response.parsed_json is None:
            errors.append(f"Run {run_idx}: {response.error}")
            if verbose:
                print(f"ERROR")
            continue
        
        methods = extract_top_k_methods(response)
        all_runs.append({"run": run_idx, "methods": methods})
        
        if verbose:
            print(f"{len(methods)} methods")
        
        time.sleep(0.1)
    
    # Aggregate results
    aggregated = _aggregate_results(all_runs, top_k)
    
    result = InferenceResult(
        final_ranking=aggregated, iterations_used=num_runs,
        converged=True, all_iterations=all_runs,
        errors=errors, total_latency_seconds=total_latency
    )
    _save_result(result, output_dir)
    return result


def extract_expected_behavior(
    client: OllamaClient,
    prompt_builder: PromptBuilder,
    failing_test: str,
    test_code_snippet: str,
    output_dir: str,
    temperature: float = 0.2,
    verbose: bool = True
) -> List[str]:
    """Extract expected behavior (Template 2 Step 4A)."""
    if verbose:
        print("  Extracting expected behavior...", end=" ", flush=True)
    
    prompt = prompt_builder.build_template2_step4a(failing_test, test_code_snippet)
    response = client.generate(prompt=prompt, temperature=temperature)
    
    if output_dir:
        ensure_dir(output_dir)
        with open(os.path.join(output_dir, f"expected_behavior_{timestamp()}.txt"), "w", encoding="utf-8") as f:
            f.write(response.raw_text)
    
    if response.parsed_json is None:
        if verbose:
            print("ERROR")
        return []
    
    bullets = response.parsed_json.get("expected_behavior", [])
    bullets = [str(b).strip() for b in bullets if str(b).strip()][:6]
    
    if verbose:
        print(f"{len(bullets)} bullets")
    
    return bullets


def _aggregate_results(runs: List[Dict], top_k: int) -> List[Dict[str, str]]:
    """Aggregate self-consistency runs."""
    stats: Dict[str, Dict] = {}
    
    for run in runs:
        for rank, item in enumerate(run.get("methods", []), start=1):
            method = item.get("method", "")
            if not method:
                continue
            
            if method not in stats:
                stats[method] = {"count": 0, "ranks": [], "justifications": []}
            
            stats[method]["count"] += 1
            stats[method]["ranks"].append(rank)
            if item.get("justification"):
                stats[method]["justifications"].append(item["justification"])
    
    items = []
    for method, s in stats.items():
        avg_rank = sum(s["ranks"]) / len(s["ranks"])
        justification = min(s["justifications"], key=len) if s["justifications"] else ""
        items.append((method, s["count"], avg_rank, justification))
    
    items.sort(key=lambda x: (-x[1], x[2]))
    
    return [{"method": m, "justification": j} for m, _, _, j in items[:top_k]]


def _save_result(result: InferenceResult, output_dir: str) -> None:
    """Save inference result to JSON."""
    output_data = {
        "top_k": result.final_ranking,
        "metadata": {
            "iterations_used": result.iterations_used,
            "converged": result.converged,
            "total_latency_seconds": result.total_latency_seconds,
            "errors": result.errors
        }
    }
    
    if result.expected_behavior:
        output_data["expected_behavior"] = result.expected_behavior
    
    with open(os.path.join(output_dir, f"final_{timestamp()}.json"), "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
