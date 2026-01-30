# Results Directory

This directory contains the **aggregated experimental results** and evaluation metrics for fault localization experiments on Java (Defects4J) and Python (BugsInPy) benchmarks.

## 📁 Structure

```
results/
├── java/
│   └── java_results.txt
└── python/
    └── python_results.txt
```

## 📊 Results Format

Each results file contains classification metrics at K=5 for all projects and bugs analyzed.

### Metrics Reported

For each project:
- **Top-1 Hits**: Number of bugs where buggy method ranked #1
- **Top-3 Hits**: Number of bugs where buggy method in top 3
- **Top-5 Hits**: Number of bugs where buggy method in top 5
- **Mean Precision**: TP / (TP + FP) averaged across bugs
- **Mean Recall**: TP / (TP + FN) averaged across bugs
- **Mean F1 Score**: Harmonic mean of precision and recall
- **Mean Accuracy**: (TP + TN) / Total averaged across bugs

### Global Averages
- **Total Bugs Processed**: Sum across all projects
- **Average F1 Score**: Weighted average by number of bugs
- **Average Accuracy**: Weighted average by number of bugs

- Use same random seed if applicable
- Check normalization logic matches paper
