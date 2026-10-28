# Learning Analytics Engine



A Python and SQLite analytics pipeline for generating learning-platform data, validating database integrity, detecting anomalous records, and producing structured analytics reports.



## Project Overview



The Learning Analytics Engine simulates a learning management system (LMS) and turns its data into actionable reporting metrics.



The project covers the data lifecycle:



1\. Generate learners, courses, assessments, enrollments, activity events, and course outcomes.

2\. Persist generated records in a relational SQLite database.

3\. Validate required data fields and foreign-key relationships.

4\. Detect anomalous activity events and suspicious completion outcomes.

5\. Calculate course completion, assessment performance, and learner engagement metrics.

6\. Export analytics and anomaly findings to JSON.

7\. Run automated tests for correctness and reproducibility.



## Current Project Results



The pipeline has been verified with the following generated dataset:



| Metric | Count |

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



The analytics report previously recorded 58 completed enrollments and a completion rate of 15.03%.



These values describe the current generated dataset and are not production LMS statistics.



## Technology Stack



\- \*\*Language:\*\* Python

\- \*\*Database:\*\* SQLite

\- \*\*Data analysis:\*\* SQL

\- \*\*Reporting:\*\* JSON

\- \*\*Testing:\*\* pytest

\- \*\*Version control:\*\* Git (to be initialized for this project)



## Architecture



```text

Data Generators

&#x20;     |

&#x20;     v

SQLite Database

&#x20;     |

&#x20;     +----------------------+

&#x20;     |                      |

&#x20;     v                      v

Data Integrity Checks   Anomaly Detection

&#x20;     |                      |

&#x20;     +-----------+----------+

&#x20;                 |

&#x20;                 v

&#x20;        Analytics Reporting

&#x20;                 |

&#x20;                 v

&#x20;            JSON Report

```



## Project Structure



```text

learning-analytics-engine/

â”œâ”€â”€ data/

â”‚   â””â”€â”€ ground\_truth/

â”œâ”€â”€ docs/

â”‚   â”œâ”€â”€ business\_rules.md

â”‚   â”œâ”€â”€ data\_dictionary.md

â”‚   â””â”€â”€ er\_diagram.md

â”œâ”€â”€ reports/

â”œâ”€â”€ src/

â”‚   â”œâ”€â”€ database/

â”‚   â”œâ”€â”€ generator/

â”‚   â”œâ”€â”€ reporting/

â”‚   â”œâ”€â”€ validation/

â”‚   â””â”€â”€ build\_pipeline.py

â”œâ”€â”€ tests/

â”œâ”€â”€ requirements.txt

â””â”€â”€ README.md

```



## Features



### 1. Data Generation Pipeline



Generates reproducible sample data for learners, courses, cohorts, content, assessments, enrollments, activity events, attempts, and course outcomes.



The pipeline accepts a configurable database path and refuses to rebuild over an existing database file.



### 2. Data Integrity Validation



Checks database relationships and expected data structure, including:



\- Foreign-key violations

\- Missing required values

\- Required tables and columns

\- Duplicate source event identifiers



### 3. Anomaly Detection



The anomaly detector currently checks for:



\- Duplicate activity events

\- Activity events without a valid enrollment

\- Completed outcomes without a passing required assessment

\- Activity timestamps whose local date differs from their UTC date



The findings include a record identifier, issue type, and descriptive details.



### 4. Analytics Reporting



The JSON report contains:



\- Overall dataset metrics

\- Course completion metrics

\- Assessment performance

\- Learner engagement

\- Data-quality checks

\- Anomaly findings grouped by issue type



Anomaly status is reported as `clean` when no findings exist, or `needs\_investigation` when findings are present.



### 5. Automated Testing



The pytest suite covers:



\- Anomaly detector behavior

\- Detection of injected anomalies

\- Database integrity

\- Reporting metrics

\- Report safety

\- Anomaly reporting

\- Reproducibility



\*\*Latest verified result:\*\* 22 tests passed. Rerun the suite after making further changes to confirm the current result.



## Getting Started



### Prerequisites



\- Python 3.11 or a compatible Python version

\- PowerShell on Windows, or an equivalent terminal on another operating system



### 1. Create and activate a virtual environment



On Windows PowerShell:



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

```



### 2. Install dependencies



```powershell

python -m pip install -r requirements.txt

```



### 3. Run the test suite



```powershell

python -m pytest .\\tests -v

```



### 4. Build a database



The pipeline refuses to overwrite an existing database. Select a new path for every fresh build.



```powershell

$env:LEARNING\_ANALYTICS\_DB = (Join-Path (Get-Location) "data\\readme\_demo.db")

python -m src.build\_pipeline

```



This example uses `data\\readme\_demo.db`. If that file already exists, choose another filename instead.



### 5. Generate an analytics report



The report generator also refuses to overwrite an existing report. The following example uses a new output filename.



```powershell

python -c "from src.reporting.generate\_report import build\_report, write\_report; from pathlib import Path; db=Path('data/readme\_demo.db').resolve(); report=build\_report(db); write\_report(report, Path('reports/readme\_demo\_report.json'))"

```



If the example database or report already exists, choose another filename. The database path passed to `build\_report` determines which database is analyzed.



The report is written as JSON and includes data-quality and anomaly summaries.



## Documentation



\- \[Business Rules](docs/business\_rules.md)

\- \[Data Dictionary](docs/data\_dictionary.md)

\- \[ER Diagram](docs/er\_diagram.md)



## Current Limitations



\- The dataset is synthetic and intended for development and testing.

\- The current report is a JSON artifact rather than a deployed dashboard.

\- Anomaly rules are deterministic checks, not a trained machine-learning anomaly classifier.

\- The report's data-quality checks cover the implemented rules and do not guarantee that every business rule is satisfied.

\- The project has not yet been documented here as a deployed production service.



## Future Improvements



\- Add an ER diagram showing database entities and relationships.

\- Expand data-quality rules and anomaly tests.

\- Add time-based learner engagement trends.

\- Build an interactive dashboard.

\- Add structured logging and configurable report outputs.

\- Add a continuous integration workflow to run tests automatically.



## Author



Developed as a learning analytics and data engineering portfolio project.
