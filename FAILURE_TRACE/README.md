# FAILURE_TRACE Directory

This directory contains **execution traces and stack traces** from failing test runs. Each bug has test execution metadata including which tests failed and their complete stack traces.

## 📁 Structure

```
FAILURE_TRACE/
└── <Project>/
    └── <bug_id>/
        └── tests.csv
```


## 📝 File Format

Each `tests.csv` file contains test execution results with the following columns:

```csv
name,outcome,runtime,stacktrace
```

### Column Descriptions

| Column | Type | Description |
|--------|------|-------------|
| `name` | string | Fully qualified test method name |
| `outcome` | string | Test result: `PASS`, `FAIL`, or `ERROR` |
| `runtime` | float | Test execution time in seconds |
| `stacktrace` | string | Full stack trace for failed tests (empty for passing tests) |


## 🔨 Data Collection

### For Java (Defects4J)

Tests are executed using Defects4J's built-in test runner:

```bash
# Checkout buggy version
defects4j checkout -p Math -v 1b -w /tmp/math_1

# Run tests
cd /tmp/math_1
defects4j test

# Collect traces
defects4j export -p tests.trigger  # Get failing tests
# Parse test output and stack traces
```

### For Python (BugsInPy)

Tests are executed using BugsInPy's testing framework:

```bash
# Checkout buggy version
bugsinpy-checkout -p black -v 1 -w /tmp/black_1

# Run tests
cd /tmp/black_1
bugsinpy-test

# Collect traces from pytest output
```
