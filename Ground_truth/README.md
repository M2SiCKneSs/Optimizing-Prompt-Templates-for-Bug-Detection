# Ground Truth Directory

This directory contains the **ground truth buggy methods** for each project. These files serve as the gold standard for evaluating fault localization performance.

## 📁 Structure

```
ground_truth/
├── <project>_ground_truth.txt
```

### Files

**Java Projects (Defects4J):**
- `Math_ground_truth.txt`
- `Lang_ground_truth.txt`
- `Chart_ground_truth.txt`
- `Time_ground_truth.txt`

**Python Projects (BugsInPy):**
- `black_ground_truth.txt`
- `thefuck_ground_truth.txt`
- `tqdm_ground_truth.txt`

## 📝 File Format

Each line in a ground truth file maps a bug ID to its buggy method:

```
<bug_id> : <fully_qualified_method_signature>
```

### Format Rules

1. **Bug ID**: Integer identifier (1, 2, 3, ...)
2. **Separator**: Space-colon-space (` : `)
3. **Method Signature**: Fully qualified method name with parameters
4. **Comments**: Lines starting with `#` are ignored
5. **Empty Lines**: Blank lines are ignored


## 🔧 Method Signature Conventions

### Python Methods

**Module-level function:**
```
<module>##<function_name>(<params>)
```
Example: `tqdm.contrib.__init__##tenumerate(iterable,start,total,tqdm_class,**tqdm_kwargs)`

**Class method:**
```
<module>$<ClassName>#<method_name>(<params>)
```
Example: `tqdm.std$tqdm#print_status(s)`

**Leading dots** (`.`) indicate relative imports or nested modules.

### Java Methods

**Standard format:**
```
<package>.<ClassName>.<methodName>(<ParamType1>,<ParamType2>,...)
```

**Examples:**
```
org.apache.commons.math3.fraction.Fraction.Fraction(double,int)
org.joda.time.field.UnsupportedDurationField.compareTo(DurationField)
org.jfree.chart.plot.CategoryPlot.setRenderer(int,CategoryItemRenderer,boolean)
```

## 📋 Data Sources

### Defects4J (Java)

Ground truth extracted from Defects4J metadata:
- Bug patch files analyzed to identify changed methods
- Developer notes and commit messages
- Manual verification by benchmark creators

### BugsInPy (Python)

Ground truth extracted from:
- Git diff between buggy and fixed commits
- BugsInPy's bug classification metadata
- Manual annotation for complex multi-method bugs
