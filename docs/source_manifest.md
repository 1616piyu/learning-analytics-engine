# Synthetic Dataset Source Manifest

## Data origin
All learner, course, enrollment, activity, assessment, and outcome
records are synthetically generated for this engineering challenge.
No real learner records or external production datasets are used.

## Reproducibility configuration
- Random seed: `20261022`
- Reference timestamp: `2026-10-22T12:00:00+00:00`
- Full-scale database: `data/learning_analytics_full.db`
- CSV, SQL, and JSON exports: `data/exports/`

## Full-scale targets
| Entity | Target records |
|---|---:|
| Learner | 20,000 |
| Course | 500 |
| Enrollment | 100,000 |
| ActivityEvent | 2,000,000 |

## Generation commands
Starter database:
`python -m src.build_pipeline --scale starter --db .\data\starter_submission.db`

Full database:
`python -m src.build_pipeline --scale full --db .\data\learning_analytics_full.db`

Export the full database:
`python -m src.export_dataset`

Run tests:
`python -m pytest -q`

## Validation evidence
The full-scale build reported the target counts and passed its foreign-key check.
A separate database validation reported:
- All four target counts matched.
- No duplicate IDs in Learner, Course, Enrollment, or ActivityEvent.
- Zero foreign-key violations.

## Anomaly handling
The baseline database and its exports represent generated baseline data.
Injected anomalies and their ground-truth labels must be maintained separately.
Ground-truth labels are evaluation metadata and must not be used as detector features.

## Export integrity
`data/exports/export_manifest.json` records the exported table row counts,
file sizes, and SHA-256 checksums. Regenerate exports after changing the
source database.
