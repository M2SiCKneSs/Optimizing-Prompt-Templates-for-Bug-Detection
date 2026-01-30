"""
Evaluation module for LLM-based Fault Localization.
Computes metrics (Top-K, Precision, Recall, F1, Accuracy) and generates reports.
"""

import os
from typing import List, Dict, Set
from collections import defaultdict


def normalize_method(method: str) -> str:
    """Normalize method name for comparison."""
    method = method.strip()
    for sep in ["#", "::", "."]:
        if sep in method:
            method = method.rsplit(sep, 1)[-1]
    if "(" in method:
        method = method.split("(")[0]
    return method.lower()


def evaluate_bug(predicted: List[str], actual: Set[str], k: int = 5) -> Dict:
    """
    Evaluate predictions for a single bug.
    
    Args:
        predicted: List of predicted method names (ranked)
        actual: Set of actual buggy method names
        k: Top-K cutoff for evaluation
    
    Returns:
        Dict with metrics: top_1, top_3, top_5, precision, recall, f1, accuracy
    """
    pred_norm = [normalize_method(m) for m in predicted[:k]]
    actual_norm = {normalize_method(m) for m in actual}
    
    pred_set = set(pred_norm)
    
    tp = len(pred_set & actual_norm)
    fp = len(pred_set - actual_norm)
    fn = len(actual_norm - pred_set)
    tn = max(0, k - tp - fp)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / k if k > 0 else 0.0
    
    # Top-K hits
    top_1 = bool(set(pred_norm[:1]) & actual_norm)
    top_3 = bool(set(pred_norm[:3]) & actual_norm)
    top_5 = bool(set(pred_norm[:5]) & actual_norm)
    
    return {
        "top_1": top_1,
        "top_3": top_3,
        "top_5": top_5,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy
    }


def generate_evaluation_report(
    results: List[tuple],
    ground_truth: Dict[str, Dict[int, Set[str]]],
    k: int = 5,
    benchmark_type: str = "python"
) -> str:
    """
    Generate evaluation report in the standard format.
    
    Args:
        results: List of (project, bug_id, result_data) tuples
        ground_truth: Dict mapping project -> bug_id -> set of buggy methods
        k: Top-K cutoff
        benchmark_type: "python" (BugsInPy) or "java" (Defects4J)
    
    Returns:
        Formatted report string
    """
    # Group results by project
    project_results: Dict[str, List[Dict]] = defaultdict(list)
    
    for project, bug_id, result_data in results:
        actual = ground_truth.get(project, {}).get(bug_id, set())
        if isinstance(actual, list):
            actual = set(actual)
        
        if not actual:
            continue  # Skip bugs without ground truth
        
        predicted = [m.get("method", "") for m in result_data.get("top_k", [])]
        metrics = evaluate_bug(predicted, actual, k)
        metrics["project"] = project
        metrics["bug_id"] = bug_id
        
        project_results[project].append(metrics)
    
    # Build report
    lines = []
    
    if benchmark_type == "python":
        lines.append(f"BugsInPy Classification Metrics (K={k})")
    else:
        lines.append(f"Fault Localization Evaluation (K={k})")
    
    lines.append("=" * 50)
    lines.append("")
    
    total_bugs = 0
    total_top1 = 0
    total_top3 = 0
    total_top5 = 0
    total_precision = 0.0
    total_recall = 0.0
    total_f1 = 0.0
    total_accuracy = 0.0
    
    for project in sorted(project_results.keys()):
        bugs = project_results[project]
        n_bugs = len(bugs)
        
        if n_bugs == 0:
            continue
        
        top1 = sum(1 for b in bugs if b["top_1"])
        top3 = sum(1 for b in bugs if b["top_3"])
        top5 = sum(1 for b in bugs if b["top_5"])
        
        mean_prec = sum(b["precision"] for b in bugs) / n_bugs
        mean_rec = sum(b["recall"] for b in bugs) / n_bugs
        mean_f1 = sum(b["f1"] for b in bugs) / n_bugs
        mean_acc = sum(b["accuracy"] for b in bugs) / n_bugs
        
        lines.append(f"Project: {project.lower()} ({n_bugs} bugs analyzed)")
        lines.append(f"  Top-1 Hits: {top1}")
        lines.append(f"  Top-3 Hits: {top3}")
        lines.append(f"  Top-5 Hits: {top5}")
        lines.append(f"  Mean Precision: {mean_prec:.4f}")
        lines.append(f"  Mean Recall:    {mean_rec:.4f}")
        lines.append(f"  Mean F1 Score:  {mean_f1:.4f}")
        lines.append(f"  Mean Accuracy:  {mean_acc:.4f}")
        lines.append("")
        
        total_bugs += n_bugs
        total_top1 += top1
        total_top3 += top3
        total_top5 += top5
        total_precision += mean_prec * n_bugs
        total_recall += mean_rec * n_bugs
        total_f1 += mean_f1 * n_bugs
        total_accuracy += mean_acc * n_bugs
    
    # Global averages
    if benchmark_type == "python":
        lines.append("GLOBAL AVERAGES")
    else:
        lines.append("OVERALL TOTALS")
    
    lines.append("-" * 15)
    
    if benchmark_type == "python":
        lines.append(f"Total Bugs Processed: {total_bugs}")
        if total_bugs > 0:
            lines.append(f"Average F1 Score:     {total_f1 / total_bugs:.4f}")
            lines.append(f"Average Accuracy:     {total_accuracy / total_bugs:.4f}")
    else:
        lines.append(f"Total Bugs Analyzed: {total_bugs}")
        lines.append(f"Total Top-1: {total_top1}")
        lines.append(f"Total Top-3: {total_top3}")
        lines.append(f"Total Top-5: {total_top5}")
        if total_bugs > 0:
            lines.append(f"Average Precision: {total_precision / total_bugs:.4f}")
            lines.append(f"Average Recall:    {total_recall / total_bugs:.4f}")
            lines.append(f"Average F1:        {total_f1 / total_bugs:.4f}")
            lines.append(f"Average Accuracy:  {total_accuracy / total_bugs:.4f}")
    
    return "\n".join(lines)


def save_report(report: str, output_path: str) -> None:
    """Save report to file."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
