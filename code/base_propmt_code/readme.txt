README - Base Prompt Construction Pipeline

Purpose

Build the “base prompt” files used by the LLM experiments in Section 4.

The pipeline collects, for each bug:

BUG_REPORT (title + description)

FAILING_TEST (top-N failing functions from FAILING_TEST files)

CODE_SNIPPETS (Java snippets for those functions)

FAILURE_TRACE (stacktraces from FAILURE_TRACE/tests.csv where outcome=FAIL)

Output

Base prompts are created here:
prompts<Project>\base_prompt_<Project>-<id>.txt
Example:
prompts\Math\base_prompt_Math-1.txt
prompts\Chart\base_prompt_Chart-10.txt

Prerequisites

Folder layout exists under:
C:\Users\user\Desktop\uni\mark\

BUG_REPORT\

FAILING_TEST\

CODE_SNIPPETS\

FAILURE_TRACE\

prompts\ (will be created/filled)

Activate venv and install dependencies:
cd C:\Users\user\Desktop\uni\mark
..venv\Scripts\activate

(These scripts only use standard library Python; no extra pip packages required.)

Pipeline order (must run in this order)

build_all_base_prompts_bug_report.py

Scans BUG_REPORT<Project>*.json

Creates initial base prompts containing only:

BUG_REPORT

Title: ...
Description: ...

enrich_base_prompts_with_tests_and_snippets.py

Scans FAILING_TEST<Project><Project>-<id>.txt

Takes top-N functions (default N=10)

Locates source files under CODE_SNIPPETS<Project>...

Lang/Math/Time: CODE_SNIPPETS<Project>\src\main\java\org...

Chart: CODE_SNIPPETS\Chart\source\org...

Appends:

FAILING_TEST
CODE_SNIPPETS

IMPORTANT: Only updates bugs that already have a base prompt file.
(If a failing test exists for a bug with no base prompt, it is skipped.)

append_failure_trace_to_all_base_prompts.py

Scans FAILURE_TRACE<Project><id>\tests.csv

Filters rows with outcome=FAIL

Appends:

FAILURE_TRACE

IMPORTANT: Only updates bugs that already have a base prompt file.

How to run (manual)
From:
C:\Users\user\Desktop\uni\mark

Create base prompts from bug reports:
python build_all_base_prompts_bug_report.py

Add failing test functions + code snippets:
python enrich_base_prompts_with_tests_and_snippets.py --top_n 10

Add failure traces:
python append_failure_trace_to_all_base_prompts.py

How to run (recommended: wrapper)
If you created run_pipeline.py (the wrapper that runs the 3 scripts in order):
python run_pipeline.py

What “success” looks like

After running the pipeline you should see, for each project:
prompts<Project>\base_prompt_<Project>-<id>.txt

Each base prompt should contain these sections (in this order):

BUG_REPORT
FAILING_TEST
CODE_SNIPPETS
FAILURE_TRACE