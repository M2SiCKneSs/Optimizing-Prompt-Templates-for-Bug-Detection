import os
import csv
import glob
import argparse

BASE_DIR = r"C:\Users\user\Desktop\uni\mark"
FAILURE_TRACE_DIR = os.path.join(BASE_DIR, "FAILURE_TRACE")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")

BASE_PROMPT_BASENAME_FMT = "base_prompt_{project}-{bug_id}.txt"


def base_prompt_path_if_exists(project: str, bug_id: int):
    path = os.path.join(
        PROMPTS_DIR,
        project,
        BASE_PROMPT_BASENAME_FMT.format(project=project, bug_id=bug_id),
    )
    return path if os.path.isfile(path) else None


def append_failure_traces(prompt_path: str, failing_rows: list) -> None:
    with open(prompt_path, "a", encoding="utf-8") as f:
        f.write("\n\n### FAILURE_TRACE\n")
        if not failing_rows:
            f.write("(No failing stacktraces found in tests.csv)\n")
            return

        for i, row in enumerate(failing_rows, start=1):
            name = (row.get("name") or "").strip()
            runtime = (row.get("runtime") or "").strip()
            stacktrace = (row.get("stacktrace") or "").strip()

            f.write("\n" + "-" * 90 + "\n")
            f.write(f"Fail #{i}\n")
            f.write(f"Test: {name}\n")
            if runtime:
                f.write(f"Runtime: {runtime}\n")
            f.write("-" * 90 + "\n")
            f.write(stacktrace if stacktrace else "(empty stacktrace)")
            f.write("\n")


def read_failing_rows_from_tests_csv(tests_csv_path: str) -> list:
    failing = []
    with open(tests_csv_path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            outcome = (row.get("outcome") or "").strip().upper()
            if outcome == "FAIL":
                failing.append(row)
    return failing


def process_all_projects() -> None:
    if not os.path.isdir(FAILURE_TRACE_DIR):
        raise SystemExit(f"FAILURE_TRACE directory not found: {FAILURE_TRACE_DIR}")

    project_dirs = sorted([d for d in glob.glob(os.path.join(FAILURE_TRACE_DIR, "*")) if os.path.isdir(d)])
    if not project_dirs:
        raise SystemExit(f"No project folders found under: {FAILURE_TRACE_DIR}")

    total_updated = 0
    total_skipped_no_base = 0
    total_skipped_no_tests_csv = 0

    for project_dir in project_dirs:
        project = os.path.basename(project_dir)

        bug_dirs = sorted(
            [d for d in glob.glob(os.path.join(project_dir, "*")) if os.path.isdir(d)],
            key=lambda p: int(os.path.basename(p)) if os.path.basename(p).isdigit() else 10**12
        )

        for bug_dir in bug_dirs:
            bug_name = os.path.basename(bug_dir)
            if not bug_name.isdigit():
                continue

            bug_id = int(bug_name)
            tests_csv_path = os.path.join(bug_dir, "tests.csv")

            if not os.path.isfile(tests_csv_path):
                total_skipped_no_tests_csv += 1
                continue

            base_prompt_path = base_prompt_path_if_exists(project, bug_id)
            if base_prompt_path is None:
                total_skipped_no_base += 1
                continue

            failing_rows = read_failing_rows_from_tests_csv(tests_csv_path)
            append_failure_traces(base_prompt_path, failing_rows)
            total_updated += 1
            print(f"[OK] {project}-{bug_id}: appended traces -> {base_prompt_path}")

    print("\nDone.")
    print(f"Updated base prompts: {total_updated}")
    print(f"Skipped (no base prompt): {total_skipped_no_base}")
    print(f"Skipped (missing tests.csv): {total_skipped_no_tests_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scan FAILURE_TRACE for all projects and append FAIL stacktraces into existing base prompt files."
    )
    args = parser.parse_args()
    process_all_projects()
