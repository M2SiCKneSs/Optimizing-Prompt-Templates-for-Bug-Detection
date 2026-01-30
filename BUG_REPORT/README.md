# BUG_REPORT Directory

This directory contains **bug report metadata** in JSON format for each bug in the dataset. These reports provide high-level descriptions of the bug symptoms, expected behavior, and reproduction steps.

## 📁 Structure

```
BUG_REPORT/
└── <Project>/
    └── <Project>-<bug_id>.json
```

## 📝 File Format

Each JSON file contains structured bug report information:

```json
{
  "title": "<short bug description>",
  "description": "<detailed bug report>",
  "report_url": "<optional link to original issue>",
  "fix_commit": "<optional commit hash of fix>",
  "bug_type": "<optional classification>",
  "severity": "<optional severity level>"
}
```


## 🔨 Data Collection

### Source: Issue Trackers

Bug reports are extracted from:

**Java Projects (Defects4J):**
- Apache JIRA (Math, Lang)
- GitHub Issues (Chart, Time - if migrated)
- Defects4J metadata files

**Python Projects (BugsInPy):**
- GitHub Issues
- BugsInPy annotations

