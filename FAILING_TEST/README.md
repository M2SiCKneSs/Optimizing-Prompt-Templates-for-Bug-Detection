# FAILING_TEST & CODE_SNIPPETS Directories

These directories contain complementary data for fault localization:
- **FAILING_TEST**: Lists of methods that failed during test execution
- **CODE_SNIPPETS**: Source code for the candidate buggy methods

## 📁 FAILING_TEST Structure

```
FAILING_TEST/
└── <Project>/
    └── <Project>-<bug_id>.txt
```

### Format

Each file contains a ranked list of suspicious methods (one per line):

```
<fully.qualified.method.name>(<parameters>)
<fully.qualified.method.name>(<parameters>)
...
```


## 📁 CODE_SNIPPETS Structure

```
CODE_SNIPPETS/
└── <Project>/
    ├── src/main/java/org/...   # Java projects (Lang, Math, Time)
    ├── source/org/...           # Chart project
    └── <module>/<file>.py       # Python projects
```

### Java Projects

**Standard Maven Layout (Lang, Math, Time):**
```
CODE_SNIPPETS/Math/
└── src/
    └── main/
        └── java/
            └── org/
                └── apache/
                    └── commons/
                        └── math3/
                            └── fraction/
                                └── Fraction.java
```

**Chart Project Layout:**
```
CODE_SNIPPETS/Chart/
└── source/
    └── org/
        └── jfree/
            └── chart/
                ├── plot/
                │   └── CategoryPlot.java
                └── renderer/
                    └── category/
                        └── AbstractCategoryItemRenderer.java
```

### Python Projects

```
CODE_SNIPPETS/black/
└── black.py
```

```
CODE_SNIPPETS/tqdm/
├── tqdm/
│   ├── __init__.py
│   ├── _tqdm.py
│   ├── std.py
│   └── contrib/
│       └── __init__.py
└── ...
```

## 🔨 FAILING_TEST Generation

### Source: SBFL (Spectrum-Based Fault Localization)

Failing test lists are typically generated using:

1. **Coverage Collection**: Run test suite, record which methods each test executes
2. **SBFL Formula**: Apply Ochiai, Tarantula, or similar formula:

```
Ochiai(m) = failed(m) / √(totalFailed × (failed(m) + passed(m)))

where:
- failed(m) = # of failing tests that execute method m
- passed(m) = # of passing tests that execute method m
- totalFailed = total # of failing tests
```

### Tools Used

**Java (Defects4J):**
- **GZoltar**: Java coverage and SBFL tool
  ```bash
  # Instrument code
  gzoltar instrument --project-dir /path/to/project
  
  # Run tests
  gzoltar test
  
  # Generate SBFL ranking
  gzoltar fl --formula ochiai > failing_methods.txt
  ```

**Python (BugsInPy):**
- **Coverage.py** + custom SBFL implementation
  ```bash
  # Collect coverage
  coverage run -m pytest
  
  # Generate SBFL scores
  python compute_sbfl.py --formula ochiai > failing_methods.txt
  ```

