"""
Prompt templates for LLM-based Fault Localization.
Templates 1, 2, 3 as defined in PDF Section 4.3.
"""

from typing import List

# =========================
# Shared JSON Output Schema (PDF Section 4.3.1.4)
# =========================

JSON_OUTPUT_SCHEMA = """{
  "top_k": [
    {
      "method": "<method_signature>",
      "justification": "<short evidence-based explanation>"
    }
  ]
}"""


# =========================
# Template 1: Trace-aware ranking (PDF Section 4.3.1.5)
# =========================

TEMPLATE_1_PROMPT = """You are debugging a failing test.

Bug report:
{BUG_REPORT}

Failing test:
{FAILING_TEST}

Failure trace:
{FAILURE_TRACE}

Candidate methods:
{CODE_SNIPPETS}

Using the failure trace, rank the top-{K} most suspicious methods. Focus on methods that were executed during the failing run.

Output format:
{OUTPUT_SCHEMA}"""


# =========================
# Template 2: Trace + Expected Behavior (PDF Section 4.3.1.6)
# =========================

TEMPLATE_2_STEP_4A = """You are given the code of a failing test case.

Summarize the expected behavior of the system under test in plain English.

Test name:
{FAILING_TEST}

Test code:
{TEST_CODE_SNIPPET}

Write 3-6 short bullet points describing:
- Preconditions / inputs set by the test
- The action performed (what is called)
- The expected outputs / postconditions (assertions)

Do not propose fixes. Do not discuss implementation details.

Output strictly in JSON using the following schema:
{{
  "expected_behavior": [
    "<bullet 1>",
    "<bullet 2>"
  ]
}}"""

TEMPLATE_2_PROMPT = """You are debugging a failing test by comparing expected and observed behavior.

Bug report:
{BUG_REPORT}

Failing test:
{FAILING_TEST}

Expected behavior (from the test code):
{EXPECTED_BEHAVIOR}

Observed failure trace:
{FAILURE_TRACE}

Candidate methods:
{CODE_SNIPPETS}

Identify which method is most likely responsible for the mismatch between expected and observed behavior. Rank the top-{K} most suspicious methods.

Output format:
{OUTPUT_SCHEMA}"""


# =========================
# Template 3: FlexFL-style Agent (PDF Section 4.3.1.7)
# =========================

TEMPLATE_3_PROMPT = """You are a debugging assistant of our software. You will be presented with a bug report and a trigger test. Your task is to locate the top-{K} most likely culprit methods based on the bug report and the trigger test.

Bug report:
{BUG_REPORT}

Failing test:
{FAILING_TEST}

Failure trace:
{FAILURE_TRACE}

Candidate methods:
{CODE_SNIPPETS}

Based on the available information, provide the top-{K} most likely culprit methods for the bug. Since your answer will be processed automatically, please give your answer in the format as:
{OUTPUT_SCHEMA}"""


# =========================
# Zero-shot Wrapper (PDF Section 4.3.1.1)
# =========================

ZERO_SHOT_PREFIX = """Analyze the following bug information and identify the most likely buggy methods.

Previous candidate list from last iteration:
{PREVIOUS_CANDIDATES}

"""

ZERO_SHOT_SUFFIX = """
Rank the top-{K} most suspicious methods based solely on the information provided above.

Output format:
{OUTPUT_SCHEMA}"""


# =========================
# Self-consistency Wrapper (PDF Section 4.3.1.2)
# =========================

SELF_CONSISTENCY_PREFIX = """Independently analyze the information below and identify the most likely buggy methods. Do not reference or rely on any previous analysis or outputs.

"""

SELF_CONSISTENCY_SUFFIX = """
Produce a ranked list of the top-{K} most suspicious methods.

Output format:
{OUTPUT_SCHEMA}"""


# =========================
# Prompt Builder Class
# =========================

class PromptBuilder:
    """Builds prompts from templates."""
    
    def __init__(self, k: int = 10):
        self.k = k
        self.output_schema = JSON_OUTPUT_SCHEMA
    
    def _format_bullets(self, bullets: List[str]) -> str:
        return "\n".join(f"- {b}" for b in bullets)
    
    def build_template1(self, bug_report: str, failing_test: str, 
                        failure_trace: str, code_snippets: str) -> str:
        return TEMPLATE_1_PROMPT.format(
            BUG_REPORT=bug_report, FAILING_TEST=failing_test,
            FAILURE_TRACE=failure_trace, CODE_SNIPPETS=code_snippets,
            K=self.k, OUTPUT_SCHEMA=self.output_schema
        )
    
    def build_template2_step4a(self, failing_test: str, test_code_snippet: str) -> str:
        return TEMPLATE_2_STEP_4A.format(
            FAILING_TEST=failing_test, TEST_CODE_SNIPPET=test_code_snippet
        )
    
    def build_template2(self, bug_report: str, failing_test: str,
                        expected_behavior: List[str], failure_trace: str, 
                        code_snippets: str) -> str:
        return TEMPLATE_2_PROMPT.format(
            BUG_REPORT=bug_report, FAILING_TEST=failing_test,
            EXPECTED_BEHAVIOR=self._format_bullets(expected_behavior),
            FAILURE_TRACE=failure_trace, CODE_SNIPPETS=code_snippets,
            K=self.k, OUTPUT_SCHEMA=self.output_schema
        )
    
    def build_template3(self, bug_report: str, failing_test: str,
                        failure_trace: str, code_snippets: str) -> str:
        return TEMPLATE_3_PROMPT.format(
            BUG_REPORT=bug_report, FAILING_TEST=failing_test,
            FAILURE_TRACE=failure_trace, CODE_SNIPPETS=code_snippets,
            K=self.k, OUTPUT_SCHEMA=self.output_schema
        )
    
    def wrap_zero_shot(self, base_prompt: str, previous_candidates: str = "[]") -> str:
        prefix = ZERO_SHOT_PREFIX.format(PREVIOUS_CANDIDATES=previous_candidates)
        suffix = ZERO_SHOT_SUFFIX.format(K=self.k, OUTPUT_SCHEMA=self.output_schema)
        return prefix + base_prompt + suffix
    
    def wrap_self_consistency(self, base_prompt: str) -> str:
        suffix = SELF_CONSISTENCY_SUFFIX.format(K=self.k, OUTPUT_SCHEMA=self.output_schema)
        return SELF_CONSISTENCY_PREFIX + base_prompt + suffix
