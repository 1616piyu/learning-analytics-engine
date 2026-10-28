
# Learning Analytics Engine

A Python and SQLite project that generates synthetic learning-platform data, validates database integrity, detects suspicious records, and produces structured JSON analytics reports.

**Repository:** [learning-analytics-engine](https://github.com/1616piyu/learning-analytics-engine)

## Project Overview

This project simulates a Learning Management System (LMS) and builds a data analytics pipeline around its records.

The pipeline:

1. Generates learners, courses, cohorts, content, assessments, enrollments, activity events, assessment attempts, and course outcomes.
2. Stores generated records in a relational SQLite database.
3. Validates database structure, required fields, and foreign-key relationships.
4. Detects suspicious activity events and course completion outcomes.
5. Calculates course completion, assessment performance, and learner engagement metrics.
6. Exports analytics and anomaly findings to JSON.
7. Runs automated tests to check correctness and reproducibility.

> **Note:** The dataset is synthetic and intended for development, testing, and demonstration. It does not represent production LMS statistics.

## Dataset Snapshot

One verified generated dataset contained the following records:

| Entity | Count |
|---|---:|
| Learners | 100 |
| Courses | 10 |
| Cohorts | 4 |
| Content items | 40 |
| Assessments | 10 |
| Completion rules | 10 |
| Enrollments | 386 |
| Learner-cohort memberships | 100 |
| Activity events | 695 |
| Assessment attempts | 482 |
| Course outcomes | 386 |

A previously generated report recorded 58 completed enrollments and a completion rate of 15.03%. These metrics describe that particular synthetic dataset and may change if the generator or configuration changes.

## Technology Stack

- **Language:** Python
- **Database:** SQLite
- **Querying and analytics:** SQL
- **Reporting:** JSON
- **Testing:** pytest
- **Version control:** Git and GitHub

## Architecture

```text
Synthetic Data Generators
          |
          v
     SQLite Database
          |
          +----------------------+
          |                      |
          v                      v
 Data Integrity Checks     Anomaly Detection
          |                      |
          +-----------+----------+
                      |
                      v
             Analytics Reporting
                      |
                      v
                  JSON Report
```

## Project Structure

```text
learning-analytics-engine/
├── data/
│   └── ground_truth/
│       └── ground_truth.csv
├── docs/
│   ├── business_rules.md
│   ├── data_dictionary.md
│   └── er_diagram.md
├── reports/
├── src/
│   ├── database/
│   │   ├── analytics.sql
│   │   ├── completion_metrics.sql
│   │   ├── init_db.py
│   │   └── schema.sql
│   ├── generator/
│   ├── reporting/
│   │   └── generate_report.py
│   ├── validation/
│   │   ├── anomaly_detector.py
│   │   ├── checksum.py
│   │   ├── evaluate_anomalies.py
│   │   ├── inject_anomalies.py
│   │   └── integrity.py
│   └── build_pipeline.py
├── tests/
├── requirements.txt
├── .gitignore
└── README.md
```

## Key Features

### 1. Synthetic Data Generation

- Generates reproducible sample data for a learning platform.
- Uses a fixed random seed and reference time.
- Supports a configurable SQLite database path.
- Refuses to overwrite an existing database.

### 2. Data Integrity Validation

Checks include:

- Foreign-key violations.
- Missing required values.
- Required tables and columns.
- Duplicate source-event identifiers.

### 3. Rule-Based Anomaly Detection

The detector checks for:

- Duplicate activity events.
- Activity events without a valid enrollment.
- Completed outcomes without a passing required assessment.
- Events whose local calendar date differs from their UTC calendar date.

Each finding contains a record identifier, issue type, and descriptive details.

These checks use deterministic rules; they are not a trained machine-learning anomaly classifier.

### 4. Analytics Reporting

The JSON report includes:

- Overall dataset metrics.
- Course completion metrics.
- Assessment performance.
- Learner engagement.
- Data-quality checks.
- Anomaly findings grouped by issue type.

The anomaly status is `clean` when no findings are detected and `needs_investigation` when findings are present.

### 5. Automated Testing

The test suite covers:

- Anomaly detector behavior.
- Injected anomaly detection.
- Database integrity.
- Reporting calculations.
- Report overwrite protection.
- Reproducibility.

The latest recorded local test result was **22 tests passed**. Run the tests again to verify the current version.

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

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

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
python -m pytest tests -v
```

### 5. Build a New Database

The pipeline refuses to overwrite an existing database. Choose a new filename for each fresh build.

On Windows PowerShell:

```powershell
$env:LEARNING_ANALYTICS_DB = (Join-Path (Get-Location) "data\readme_demo.db")
python -m src.build_pipeline
```

If `data\readme_demo.db` already exists, choose a different filename before running the command.

The database file is ignored by Git.

### 6. Generate a JSON Report

Use the same database path and a new report filename:

```powershell
python -c "from pathlib import Path; from src.reporting.generate_report import build_report, write_report; db=Path('data/readme_demo.db').resolve(); report=build_report(db); write_report(report, Path('reports/readme_demo_report.json'))"
```

If the report file already exists, select another output filename. The report writer intentionally refuses to overwrite existing reports.

The generated report includes dataset metrics, data-quality checks, and anomaly findings.

## Documentation

- [Business Rules](docs/business_rules.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Entity Relationship Diagram](docs/er_diagram.md)

## Current Limitations

- The dataset is synthetic.
- Reports are currently generated as JSON; a deployed dashboard is not included.
- Anomaly detection uses deterministic rules rather than a trained ML model.
- Data-quality checks cover implemented rules and cannot guarantee that every possible business rule is satisfied.
- A continuous integration workflow is not currently included.

## Future Improvements

- Add continuous integration to run tests automatically.
- Add time-based learner engagement trends.
- Compare engagement and completion across cohorts.
- Build an interactive analytics dashboard.
- Expand anomaly rules and evaluate precision and recall.
- Add structured logging and configurable report options.

## Author

Developed as a learning analytics and data engineering portfolio project.
