# Learning Analytics Engine

A reproducible synthetic learning analytics pipeline built with Python, SQLite, and SQL. It generates LMS data at starter and full scales, validates relational integrity, detects data-quality anomalies, calculates learning metrics, and exports datasets for analysis.

**Repository:** [1616piyu/learning-analytics-engine](https://github.com/1616piyu/learning-analytics-engine)

## Project Overview

The pipeline:

1. Generates learners, courses, cohorts, enrollments, content, assessments, activity events, attempts, and course outcomes.
2. Stores records in a relational SQLite database.
3. Validates database integrity and foreign-key relationships.
4. Detects duplicate activity, unenrolled activity, invalid completion outcomes, and timezone-boundary candidates.
5. Calculates course completion, assessment performance, and learner engagement metrics.
6. Exports table data as CSV and JSONL, together with a SQL seed and integrity manifest.
7. Evaluates anomaly detection against separate ground-truth labels.
8. Runs automated tests for correctness and reproducibility.

All records are synthetic. They do not represent real learners or production LMS statistics.

## Dataset Profiles

| Entity | Starter | Full |
|---|---:|---:|
| Learners | 100 | 20,000 |
| Courses | 10 | 500 |
| Cohorts | 4 | 20 |
| Content items | 40 | 2,000 |
| Assessments | 10 | 500 |
| Completion rules | 10 | 500 |
| Enrollments | 386 | 100,000 |
| Learner-cohort memberships | 100 | 20,000 |
| Activity events | 695 | 2,000,000 |
| Assessment attempts | 482 | 127,637 |
| Course outcomes | 386 | 100,000 |

The starter counts reflect the established starter configuration. The full-scale counts were verified against the generated database.

## Technology Stack

- **Language:** Python
- **Database:** SQLite
- **Analytics:** SQL
- **Export formats:** CSV, JSONL, SQL, JSON
- **Testing:** pytest
- **Version control:** Git and GitHub

## Architecture

```text
Configuration and Seed
          |
          v
Synthetic Data Generators
          |
          v
    SQLite Database
          |
          +-----------------------+
          |                       |
          v                       v
   Integrity Checks       Anomaly Detection
          |                       |
          +-----------+-----------+
                      |
                      v
             Analytics Reporting
                      |
                      v
             JSON and Data Exports
```

## Project Structure

```text
learning-analytics-engine/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ data/
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ ground_truth/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ docs/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ business_rules.md
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ data_dictionary.md
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ er_diagram.md
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ source_manifest.md
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ src/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ database/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ analytics.sql
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ completion_metrics.sql
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ init_db.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ schema.sql
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ generator/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ reporting/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ generate_report.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ validation/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ anomaly_detector.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ checksum.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ evaluate_anomalies.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ inject_anomalies.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ integrity.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ build_pipeline.py
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ export_dataset.py
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ tests/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ requirements.txt
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ .gitignore
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ README.md
```

Generated databases and export directories are recreated locally and are excluded from version control.

## Key Features

### 1. Synthetic Data Generation

- Generates reproducible sample data for a learning platform.
- Uses a fixed random seed and reference timestamp.
- Supports starter and full-scale profiles.
- Supports a configurable SQLite database path.
- Refuses to overwrite an existing database.

### 2. Data Integrity Validation

Implemented checks include:

- Foreign-key violations.
- Required tables and columns.
- Duplicate IDs in the checked entities.
- Data and business-rule constraints covered by the validation code.

### 3. Rule-Based Anomaly Detection

The detector checks for:

- Duplicate activity events based on source-event identity.
- Activity events without a valid enrollment.
- Completed outcomes without a passing required assessment.
- Timezone-boundary candidates where the local calendar date differs from the UTC date.

Timezone-boundary findings are candidates for review, not necessarily confirmed data errors. These checks use deterministic rules; they are not a trained machine-learning anomaly classifier.

### 4. Analytics Reporting

The JSON report includes:

- Overall dataset metrics.
- Course completion metrics.
- Assessment performance.
- Learner engagement.
- Data-quality checks.
- Anomaly findings grouped by issue type.

The anomaly status is `clean` when no findings are detected and `needs_investigation` when findings are present.

### 5. Dataset Exports

After generating the full-scale database, run:

```powershell
python -m src.export_dataset
```

By default, the exporter reads `data/learning_analytics_full.db` and writes to `data/exports/`.

It produces:

- **CSV:** one file per table.
- **JSONL:** one JSON record per line, in one file per table.
- **SQL seed:** `learning_analytics_seed.sql`, containing schema and table data.
- **JSON summary:** `dataset_summary.json`, containing table counts and metadata.
- **SHA-256 manifest:** `export_manifest.json`, containing row counts, columns, file sizes, and checksums for exported files.

The exporter checks foreign-key integrity before exporting and processes records in batches.

## Getting Started

### Prerequisites

- Python 3.11 or a compatible Python version.
- Git.
- PowerShell on Windows, or an equivalent terminal.

### 1. Clone the Repository

```powershell
git clone https://github.com/1616piyu/learning-analytics-engine.git
cd learning-analytics-engine
```

### 2. Create and Activate a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Run the Tests

```powershell
python -m pytest -q
```

The latest recorded local run passed **25 tests**.

### 5. Build a Database

The pipeline refuses to overwrite an existing database. Use a new filename for each build.

**Starter profile:**

```powershell
python -m src.build_pipeline --scale starter --db .\data\starter_submission.db
```

**Full-scale profile:**

```powershell
python -m src.build_pipeline --scale full --db .\data\learning_analytics_full.db
```

The full profile targets 20,000 learners, 500 courses, 100,000 enrollments, and 2,000,000 activity events. Generated database files are ignored by Git.

### 6. Generate a JSON Report

Use the database you created and a new report filename:

```powershell
python -c "from pathlib import Path; from src.reporting.generate_report import build_report, write_report; db=Path('data/learning_analytics_full.db').resolve(); report=build_report(db); write_report(report, Path('reports/full_scale_report.json'))"
```

If the report already exists, select a different output filename. The report writer intentionally refuses to overwrite existing reports.

## Anomaly Evaluation

Evaluation compares detector findings with labels stored separately from the detector features. Ground-truth labels must not be used as detector features.

After building the full-scale database, create a separate test copy:

Important: Run anomaly injection only once against a fresh copy of the full-scale database. For repeat evaluations, create a new database copy before running the injector again. The ground-truth CSV is generated by the injector and is intentionally excluded from version control.

```powershell
Copy-Item .\data\learning_analytics_full.db .\data\learning_analytics_anomaly_test.db

$env:LEARNING_ANALYTICS_DB = (Resolve-Path .\data\learning_analytics_anomaly_test.db).Path
$env:LEARNING_ANALYTICS_GROUND_TRUTH = Join-Path (Get-Location).Path "data\ground_truth\full_scale_ground_truth.csv"

python -m src.validation.inject_anomalies
python -m src.validation.evaluate_anomalies
```

Run these commands in the same PowerShell session so the environment variables remain set.

The injector creates five labelled records: two duplicate-event records, one unenrolled activity event, one invalid completion outcome, and one timezone review case.

### Recorded Evaluation

| Metric | Result |
|---|---:|
| Expected actionable labels | 4 |
| True positives | 4 |
| False positives | 0 |
| False negatives | 0 |
| Precision | 100% |
| Recall | 100% |
| Review cases detected | 1 of 1 |

These results apply to the injected test cases. They do not establish equivalent performance on every possible anomaly or real-world data.

## Full-Scale Reproducibility

Two independent full-scale builds were generated using the same configured seed and reference timestamp.

The following exports matched byte-for-byte:

- All 11 CSV files.
- All 11 JSONL files.
- The SQL seed file.

The row counts also matched across all 11 database tables.

The JSON summary checksums differed because the summary contains run-specific metadata, including the source database name and generation timestamp. Its table counts matched across both runs.

## Documentation

- [Business Rules](docs/business_rules.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Entity Relationship Diagram](docs/er_diagram.md)
- [Synthetic Dataset Source Manifest](docs/source_manifest.md)

## Validation Status

The current validation evidence includes:

- 25 passing automated tests.
- Successful full-scale generation with the target row counts.
- Zero foreign-key violations in the recorded full-scale validation.
- No duplicate IDs in the checked primary-key columns.
- Successful CSV, JSONL, SQL, and JSON summary exports.
- Matching checksums for table-data exports across two independent full-scale builds.
- 100% precision and recall on the injected actionable anomaly labels, with the review case detected.

## Current Limitations

- The dataset is synthetic.
- Anomaly detection uses deterministic rules rather than a trained ML model.
- Timezone-boundary findings require review.
- Data-quality checks cover implemented rules and cannot guarantee every possible business rule is satisfied.
- The project does not include a deployed analytics dashboard.
- Generated full-scale databases and exports are recreated locally rather than committed to the repository.

## Future Improvements

- Add continuous integration to run tests automatically.
- Expand anomaly rules and evaluate them on more varied labelled cases.
- Add time-based learner engagement trends.
- Compare engagement and completion across cohorts.
- Build an interactive analytics dashboard.
- Add structured logging and configurable report options.

## Author

Developed as a learning analytics and data engineering portfolio project.


