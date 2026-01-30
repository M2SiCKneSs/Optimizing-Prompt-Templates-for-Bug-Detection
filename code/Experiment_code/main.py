"""
Main CLI for LLM-based Fault Localization experiments.

Usage:
  python main.py run --model deepseek-coder:6.7b --template 1 --mode zero_shot
  python main.py evaluate --model deepseek-coder:6.7b --template 1 --mode zero_shot --ground-truth ground_truth.json
  python main.py list prompts
"""

import argparse
import os
import sys

from config import (
    ExperimentConfig, OUTPUTS_DIR, TEMPLATE_NAMES,
    scan_base_prompts, load_bug_data, get_output_dir,
    load_ground_truth, scan_experiment_outputs, get_project_stats, ensure_dir
)
from prompts import PromptBuilder
from engine import (
    OllamaClient, run_zero_shot_iterative, run_self_consistency,
    extract_expected_behavior
)
from evaluation import generate_evaluation_report, save_report


# =========================
# Run Command
# =========================

def run_experiment(args: argparse.Namespace) -> None:
    """Run fault localization experiment."""
    
    config = ExperimentConfig(
        model=args.model,
        template=args.template,
        mode=args.mode,
        max_iterations=args.max_iters,
        self_consistency_runs=args.runs,
        top_k=args.top_k,
        timeout_seconds=args.timeout,
        max_tokens=args.max_tokens,
        temperature_zero_shot=args.temp_zero,
        temperature_self_consistency=args.temp_sc,
        save_intermediate=not args.no_intermediate,
        verbose=not args.quiet
    )
    
    print(f"Scanning prompts...")
    refs = scan_base_prompts()
    
    if not refs:
        print("ERROR: No base prompts found!")
        sys.exit(1)
    
    if args.project:
        refs = [r for r in refs if r.project in args.project]
    if args.bug_id:
        refs = [r for r in refs if r.bug_id in args.bug_id]
    
    print(f"Found {len(refs)} bugs")
    for project, count in sorted(get_project_stats(refs).items()):
        print(f"  {project}: {count}")
    
    print(f"\nInitializing {config.model}...")
    client = OllamaClient(
        model=config.model,
        timeout_seconds=config.timeout_seconds,
        max_tokens=config.max_tokens
    )
    
    if not client.is_available():
        print(f"ERROR: Ollama not available or model not found")
        sys.exit(1)
    
    prompt_builder = PromptBuilder(k=config.top_k)
    
    print(f"\nRunning: Template {config.template} / {config.mode}")
    print()
    
    success = 0
    errors = 0
    
    for i, ref in enumerate(refs, 1):
        print(f"[{i}/{len(refs)}] {ref.project}-{ref.bug_id}")
        
        try:
            bug_data = load_bug_data(ref)
            output_dir = get_output_dir(config, ref.project, ref.bug_id)
            ensure_dir(output_dir)
            
            # Build base prompt based on template
            if config.template == 1:
                base_prompt = prompt_builder.build_template1(
                    bug_data.bug_report or bug_data.raw_content,
                    bug_data.failing_test,
                    bug_data.failure_trace,
                    bug_data.code_snippets
                )
            elif config.template == 2:
                expected = extract_expected_behavior(
                    client, prompt_builder,
                    bug_data.failing_test,
                    bug_data.test_code_snippet or bug_data.failing_test,
                    output_dir, config.temperature_zero_shot, config.verbose
                ) or ["Could not extract expected behavior"]
                
                base_prompt = prompt_builder.build_template2(
                    bug_data.bug_report or bug_data.raw_content,
                    bug_data.failing_test,
                    expected,
                    bug_data.failure_trace,
                    bug_data.code_snippets
                )
            else:  # Template 3
                base_prompt = prompt_builder.build_template3(
                    bug_data.bug_report or bug_data.raw_content,
                    bug_data.failing_test,
                    bug_data.failure_trace,
                    bug_data.code_snippets
                )
            
            # Run inference
            if config.mode == "zero_shot":
                result = run_zero_shot_iterative(
                    client, prompt_builder, base_prompt, output_dir,
                    config.max_iterations, config.temperature_zero_shot,
                    config.save_intermediate, config.verbose
                )
            else:
                result = run_self_consistency(
                    client, prompt_builder, base_prompt, output_dir,
                    config.self_consistency_runs, config.temperature_self_consistency,
                    config.top_k, config.save_intermediate, config.verbose
                )
            
            if config.verbose and result.final_ranking:
                print(f"  -> Top: {result.final_ranking[0]['method'][:50]}...")
            
            success += 1
            
        except Exception as e:
            errors += 1
            print(f"  ERROR: {e}")
    
    print(f"\nDone: {success} success, {errors} errors")


# =========================
# Evaluate Command
# =========================

def evaluate_experiment(args: argparse.Namespace) -> None:
    """Evaluate results and generate report."""
    
    gt_path = args.ground_truth
    if not gt_path or not os.path.exists(gt_path):
        print("ERROR: Ground truth file required (--ground-truth)")
        sys.exit(1)
    
    ground_truth = load_ground_truth(gt_path)
    print(f"Loaded ground truth: {sum(len(b) for b in ground_truth.values())} bugs")
    
    results = scan_experiment_outputs(args.model, args.template, args.mode)
    
    if not results:
        print(f"ERROR: No results found for {args.model}, template {args.template}, {args.mode}")
        sys.exit(1)
    
    print(f"Found {len(results)} bug results")
    
    # Generate report
    report = generate_evaluation_report(
        results, ground_truth,
        k=args.top_k,
        benchmark_type=args.benchmark
    )
    
    print()
    print(report)
    
    if args.output:
        save_report(report, args.output)
        print(f"\nSaved to: {args.output}")


# =========================
# List Command
# =========================

def list_data(args: argparse.Namespace) -> None:
    """List available data."""
    
    if args.what == "prompts":
        refs = scan_base_prompts()
        print("Available prompts:")
        for project, count in sorted(get_project_stats(refs).items()):
            print(f"  {project}: {count} bugs")
        print(f"Total: {len(refs)} bugs")
    
    elif args.what == "experiments":
        print("Completed experiments:")
        if os.path.isdir(OUTPUTS_DIR):
            for model_dir in os.listdir(OUTPUTS_DIR):
                model_path = os.path.join(OUTPUTS_DIR, model_dir)
                if os.path.isdir(model_path):
                    print(f"  {model_dir.replace('_', ':', 1)}:")
                    for t in os.listdir(model_path):
                        t_path = os.path.join(model_path, t)
                        if os.path.isdir(t_path):
                            for m in os.listdir(t_path):
                                print(f"    {t}/{m}")


# =========================
# Main
# =========================

def main():
    parser = argparse.ArgumentParser(description="LLM Fault Localization Pipeline")
    subparsers = parser.add_subparsers(dest="command")
    
    # Run command
    run_p = subparsers.add_parser("run", help="Run experiment")
    run_p.add_argument("--model", required=True, help="Ollama model (e.g., deepseek-coder:6.7b)")
    run_p.add_argument("--template", type=int, choices=[1, 2, 3], required=True,
                       help="1=Trace-aware, 2=Trace+Expected, 3=FlexFL")
    run_p.add_argument("--mode", choices=["zero_shot", "self_consistency"], required=True)
    run_p.add_argument("--max-iters", type=int, default=10, help="Max iterations (default: 10)")
    run_p.add_argument("--runs", type=int, default=5, help="Self-consistency runs (default: 5)")
    run_p.add_argument("--top-k", type=int, default=10, help="Top-K methods (default: 10)")
    run_p.add_argument("--timeout", type=int, default=1800, help="Timeout seconds (default: 1800)")
    run_p.add_argument("--max-tokens", type=int, default=1024, help="Max tokens (default: 1024)")
    run_p.add_argument("--temp-zero", type=float, default=0.2, help="Zero-shot temp (default: 0.2)")
    run_p.add_argument("--temp-sc", type=float, default=0.7, help="Self-consistency temp (default: 0.7)")
    run_p.add_argument("--project", nargs="+", help="Filter by project(s)")
    run_p.add_argument("--bug-id", type=int, nargs="+", help="Filter by bug ID(s)")
    run_p.add_argument("--no-intermediate", action="store_true", help="Don't save intermediate files")
    run_p.add_argument("--quiet", action="store_true", help="Less output")
    
    # Evaluate command
    eval_p = subparsers.add_parser("evaluate", help="Evaluate results")
    eval_p.add_argument("--model", required=True, help="Model name")
    eval_p.add_argument("--template", type=int, choices=[1, 2, 3], required=True)
    eval_p.add_argument("--mode", choices=["zero_shot", "self_consistency"], required=True)
    eval_p.add_argument("--ground-truth", required=True, help="Ground truth JSON file")
    eval_p.add_argument("--top-k", type=int, default=5, help="Top-K for metrics (default: 5)")
    eval_p.add_argument("--benchmark", choices=["python", "java"], default="python",
                        help="Output format: python (BugsInPy) or java (Defects4J)")
    eval_p.add_argument("--output", "-o", help="Output file path")
    
    # List command
    list_p = subparsers.add_parser("list", help="List available data")
    list_p.add_argument("what", choices=["prompts", "experiments"])
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "run":
        run_experiment(args)
    elif args.command == "evaluate":
        evaluate_experiment(args)
    elif args.command == "list":
        list_data(args)


if __name__ == "__main__":
    main()
