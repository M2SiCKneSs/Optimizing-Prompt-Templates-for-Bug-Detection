# base_propmt_pipeline.py
# Runs your 3 scripts in order:
# 1) build_all_base_prompts_bug_report.py
# 2) enrich_base_prompts_with_tests_and_snippets.py
# 3) append_failure_trace_to_all_base_prompts.py

import sys
import subprocess
from pathlib import Path


SCRIPTS_IN_ORDER = [
    "build_all_base_prompts_bug_report.py",
    "enrich_base_prompts_with_tests_and_snippets.py",
    "append_failure_trace_to_all_base_prompts.py",
]


def run_script(script_path: Path) -> None:
    print(f"\n=== Running: {script_path.name} ===")
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(script_path.parent),
        capture_output=True,
        text=True,
    )

    if proc.stdout:
        print(proc.stdout)

    if proc.returncode != 0:
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        raise SystemExit(f"FAILED: {script_path.name} (exit code {proc.returncode})")

    if proc.stderr:
        # some scripts print warnings to stderr even if success
        print(proc.stderr, file=sys.stderr)

    print(f"=== OK: {script_path.name} ===")


def main() -> None:
    here = Path(__file__).resolve().parent

    for script_name in SCRIPTS_IN_ORDER:
        script_path = here / script_name
        if not script_path.is_file():
            raise SystemExit(f"Script not found: {script_path}")
        run_script(script_path)

    print("\nAll done. Pipeline completed successfully.")


if __name__ == "__main__":
    main()
