import os
import json
import glob

BUG_REPORT_DIR = r"C:\Users\user\Desktop\uni\mark\BUG_REPORT"
PROMPTS_DIR = r"C:\Users\user\Desktop\uni\mark\prompts"

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_id_from_filename(project: str, filename: str) -> int:
    # e.g., "Math-10.json" -> 10
    stem = os.path.splitext(filename)[0]
    parts = stem.split("-")
    if len(parts) < 2 or parts[0] != project:
        raise ValueError(f"Unexpected filename format: {filename}")
    return int(parts[1])

def write_base_prompt_file(project: str, json_path: str) -> str:
    data = load_json(json_path)
    title = (data.get("title") or "").strip()
    desc = (data.get("description") or "").strip()

    bug_id = extract_id_from_filename(project, os.path.basename(json_path))

    out_dir = os.path.join(PROMPTS_DIR, project)
    os.makedirs(out_dir, exist_ok=True)

    # IMPORTANT: file name is "base prompt" (as requested)
    out_path = os.path.join(out_dir, f"base_prompt_{project}-{bug_id}.txt")

    content = (
        "### BUG_REPORT\n"
        f"Title: {title}\n\n"
        "Description:\n"
        f"{desc}\n"
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    return out_path

def main() -> None:
    if not os.path.isdir(BUG_REPORT_DIR):
        raise SystemExit(f"BUG_REPORT directory not found: {BUG_REPORT_DIR}")

    # Scan all project folders (Chart, Lang, Math, Time, ...)
    project_dirs = sorted(
        [d for d in glob.glob(os.path.join(BUG_REPORT_DIR, "*")) if os.path.isdir(d)]
    )

    if not project_dirs:
        raise SystemExit(f"No project folders found under: {BUG_REPORT_DIR}")

    total_created = 0

    for project_dir in project_dirs:
        project = os.path.basename(project_dir)

        json_paths = glob.glob(os.path.join(project_dir, f"{project}-*.json"))
        if not json_paths:
            print(f"[SKIP] No JSON files found for project: {project}")
            continue

        json_paths = sorted(
            json_paths,
            key=lambda p: extract_id_from_filename(project, os.path.basename(p))
        )

        created = 0
        for jp in json_paths:
            out_path = write_base_prompt_file(project, jp)
            created += 1
            total_created += 1
            print(f"[{project}] Created: {out_path}")

        print(f"[{project}] Done. Created {created} base prompt files.\n")

    print(f"All done. Total created: {total_created}")

if __name__ == "__main__":
    main()
