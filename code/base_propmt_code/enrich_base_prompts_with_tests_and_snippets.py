import os
import re
import glob
import argparse
from typing import List, Optional, Tuple

BASE_DIR = r"C:\Users\user\Desktop\uni\mark"

FAILING_TEST_DIR = os.path.join(BASE_DIR, "FAILING_TEST")
CODE_SNIPPETS_DIR = os.path.join(BASE_DIR, "CODE_SNIPPETS")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")

# You said: process only existing BASE prompts.
# Your base prompt files are named like: prompts\<Project>\base_prompt_<Project>-<id>.txt
BASE_PROMPT_BASENAME_FMT = "base_prompt_{project}-{bug_id}.txt"


def extract_id_from_filename(project: str, filename: str) -> int:
    # e.g., "Math-10.txt" -> 10
    stem = os.path.splitext(filename)[0]
    parts = stem.split("-")
    if len(parts) < 2 or parts[0] != project:
        raise ValueError(f"Unexpected filename format: {filename}")
    return int(parts[1])


def read_first_n_nonempty_lines(path: str, n: int) -> List[str]:
    out: List[str] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            out.append(s)
            if len(out) >= n:
                break
    return out


def parse_function_line(line: str) -> Tuple[str, str]:
    """
    Examples:
      org.jfree.chart.renderer.xy.AbstractXYItemRenderer.getLegendItems()
      org.apache.commons.lang3.math.NumberUtils.createNumber(String)
      org.joda.time.field.UnsupportedDurationField.compareTo(DurationField)
      org.apache.commons.math3.fraction.Fraction.Fraction(double,int)

    Returns:
      fqcn: org....ClassName
      method: methodName OR ClassName (constructor)
    """
    m = re.match(r"^(?P<prefix>.+)\.(?P<method>[^.]+)\(.*\)\s*$", line)
    if not m:
        raise ValueError(f"Cannot parse function line: {line}")
    return m.group("prefix"), m.group("method")


def fqcn_to_java_path(code_root_org_dir: str, fqcn: str) -> str:
    """
    code_root_org_dir points to ...\org
    fqcn starts with org.
    """
    if not fqcn.startswith("org."):
        raise ValueError(f"Expected fqcn to start with 'org.': {fqcn}")
    rel = fqcn[len("org."):].replace(".", os.sep) + ".java"
    return os.path.join(code_root_org_dir, rel)


def get_code_root_org(project: str) -> Optional[str]:
    """
    New structure:
      CODE_SNIPPETS\<Project>\src\main\java\org  (Lang/Math/Time)
      CODE_SNIPPETS\<Project>\source\org         (Chart)
    """
    proj_root = os.path.join(CODE_SNIPPETS_DIR, project)
    if not os.path.isdir(proj_root):
        return None

    # Prefer Chart's "source\org" if exists
    chart_root = os.path.join(proj_root, "source", "org")
    if os.path.isdir(chart_root):
        return chart_root

    # Otherwise typical Maven layout
    maven_root = os.path.join(proj_root, "src", "main", "java", "org")
    if os.path.isdir(maven_root):
        return maven_root

    # Some projects might place code under src/test/java as well; add fallback if needed later
    return None


def read_file_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def find_method_snippet(java_text: str, class_name: str, method_name: str) -> Optional[str]:
    """
    Best-effort snippet extraction:
    - Finds a plausible declaration line for method/ctor
    - Captures block by brace counting
    """
    lines = java_text.splitlines()

    patterns = []
    if method_name == class_name:
        patterns.append(re.compile(rf"\b{re.escape(class_name)}\s*\("))
    patterns.append(re.compile(rf"\b{re.escape(method_name)}\s*\("))

    start_idx = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("//") or s.startswith("/*") or s.startswith("*"):
            continue

        if not any(p.search(line) for p in patterns):
            continue

        declish = re.search(r"\b(public|protected|private|static|final|synchronized|native|abstract)\b", line)
        annotation = s.startswith("@")
        has_block = "{" in line
        looks_like_decl = bool(declish) or annotation or has_block

        if looks_like_decl:
            start_idx = i
            break

    if start_idx is None:
        return None

    while start_idx > 0 and lines[start_idx - 1].strip().startswith("@"):
        start_idx -= 1

    snippet_lines = []
    brace_count = 0
    started = False

    for j in range(start_idx, len(lines)):
        snippet_lines.append(lines[j])

        if not started and "{" in lines[j]:
            started = True

        if started:
            brace_count += lines[j].count("{")
            brace_count -= lines[j].count("}")
            if brace_count == 0:
                break

    if not started:
        return "\n".join(snippet_lines[:3])

    return "\n".join(snippet_lines)


def append_sections_to_base_prompt(base_prompt_path: str, failing_lines: List[str], snippets: List[Tuple[str, str]]) -> None:
    with open(base_prompt_path, "a", encoding="utf-8") as f:
        f.write("\n\n### FAILING_TEST\n")
        for line in failing_lines:
            f.write(line + "\n")

        f.write("\n### CODE_SNIPPETS\n")
        for func_line, snippet in snippets:
            f.write("\n" + "-" * 90 + "\n")
            f.write(f"Function: {func_line}\n")
            f.write("-" * 90 + "\n")
            f.write(snippet.strip() + "\n")


def base_prompt_exists(project: str, bug_id: int) -> Optional[str]:
    base_dir = os.path.join(PROMPTS_DIR, project)
    base_path = os.path.join(base_dir, BASE_PROMPT_BASENAME_FMT.format(project=project, bug_id=bug_id))
    return base_path if os.path.isfile(base_path) else None


def scan_all_failing_tests(top_n: int) -> None:
    if not os.path.isdir(FAILING_TEST_DIR):
        raise SystemExit(f"FAILING_TEST directory not found: {FAILING_TEST_DIR}")

    project_dirs = sorted([d for d in glob.glob(os.path.join(FAILING_TEST_DIR, "*")) if os.path.isdir(d)])
    if not project_dirs:
        raise SystemExit(f"No project folders found under: {FAILING_TEST_DIR}")

    total_updated = 0
    total_skipped_no_base = 0
    total_skipped_no_code_root = 0

    for project_dir in project_dirs:
        project = os.path.basename(project_dir)

        # Identify code root once per project (new structure)
        code_root_org = get_code_root_org(project)
        if code_root_org is None:
            print(f"[WARN] No code root found for project '{project}' under: {os.path.join(CODE_SNIPPETS_DIR, project)}")
            total_skipped_no_code_root += 1
            continue

        failing_paths = glob.glob(os.path.join(project_dir, f"{project}-*.txt"))
        if not failing_paths:
            print(f"[SKIP] No FAILING_TEST files for project: {project}")
            continue

        failing_paths = sorted(
            failing_paths,
            key=lambda p: extract_id_from_filename(project, os.path.basename(p))
        )

        for failing_path in failing_paths:
            bug_id = extract_id_from_filename(project, os.path.basename(failing_path))

            base_prompt_path = base_prompt_exists(project, bug_id)
            if base_prompt_path is None:
                # As requested: if no base prompt exists -> skip
                total_skipped_no_base += 1
                continue

            failing_lines = read_first_n_nonempty_lines(failing_path, top_n)

            snippets: List[Tuple[str, str]] = []
            for func_line in failing_lines:
                try:
                    fqcn, method_name = parse_function_line(func_line)
                    class_name = fqcn.split(".")[-1]

                    java_path = fqcn_to_java_path(code_root_org, fqcn)
                    if not os.path.isfile(java_path):
                        snippets.append((func_line, f"[NOT FOUND] Source file not found: {java_path}"))
                        continue

                    java_text = read_file_text(java_path)
                    snippet = find_method_snippet(java_text, class_name=class_name, method_name=method_name)

                    if snippet is None:
                        snippets.append((func_line, f"[NOT FOUND] Method/ctor '{method_name}' not found in {java_path}"))
                    else:
                        snippets.append((func_line, snippet))

                except Exception as e:
                    snippets.append((func_line, f"[ERROR] {type(e).__name__}: {e}"))

            append_sections_to_base_prompt(base_prompt_path, failing_lines, snippets)
            total_updated += 1
            print(f"[OK] Updated: {base_prompt_path}")

    print("\nDone.")
    print(f"Updated base prompts: {total_updated}")
    print(f"Skipped (no base prompt): {total_skipped_no_base}")
    print(f"Skipped projects (no code root): {total_skipped_no_code_root}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scan all FAILING_TEST folders, and for existing base prompts append top-N failing functions + code snippets."
    )
    parser.add_argument("--top_n", type=int, default=10, help="How many failing functions to take (default: 10).")
    args = parser.parse_args()

    scan_all_failing_tests(top_n=args.top_n)
