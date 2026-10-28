
import json
import os
import sqlite3
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from src.reporting.business_metrics import get_cohort_performance, get_inactive_enrollment_metrics


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "learning_analytics.db"
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "learning_analytics_report.json"
)


def open_read_only_database(database_path):
    """Open an existing SQLite database without allowing writes."""
    path = Path(database_path).resolve()

    if not path.is_file():
        raise FileNotFoundError(f"Database not found: {path}")

    return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)


def get_table_counts(conn):
    """Return row counts for all application tables."""
    tables = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()

    counts = {}

    for (table_name,) in tables:
        escaped_name = table_name.replace('"', '""')
        counts[table_name] = conn.execute(
            f'SELECT COUNT(*) FROM "{escaped_name}"'
        ).fetchone()[0]

    return counts


def get_data_quality(conn, table_counts):
    """Run read-only checks for missing values and relationships."""
    checks = []

    def add_check(name, description, count, severity="warning"):
        checks.append({
            "check": name,
            "description": description,
            "issue_count": count,
            "status": "pass" if count == 0 else "fail",
            "severity": severity,
        })

    fk_violations = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    add_check(
        "foreign_key_violations",
        "Rows that violate declared foreign-key relationships.",
        len(fk_violations),
        "critical",
    )

    required_columns = {
        "Learner": [
            "learner_id", "name", "email", "created_at", "status"
        ],
        "Course": [
            "course_id", "title", "category", "status", "created_at"
        ],
        "Enrollment": [
            "enrollment_id", "learner_id", "course_id",
            "enrolled_at", "status",
        ],
        "ActivityEvent": [
            "event_id", "enrollment_id", "event_type",
            "event_time", "ingested_at", "device_type",
        ],
        "Attempt": [
            "attempt_id", "enrollment_id", "assessment_id",
            "attempt_number", "started_at", "status",
        ],
        "CourseOutcome": [
            "outcome_id", "enrollment_id", "outcome_status",
            "completion_percentage", "rule_id", "is_current",
        ],
    }

    for table_name, columns in required_columns.items():
        if table_name not in table_counts:
            add_check(
                f"table_exists_{table_name}",
                f"Required table {table_name} exists.",
                1,
                "critical",
            )
            continue

        existing_columns = {
            row[1]
            for row in conn.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()
        }

        for column_name in columns:
            if column_name not in existing_columns:
                add_check(
                    f"column_exists_{table_name}_{column_name}",
                    f"Required column {table_name}.{column_name} exists.",
                    1,
                    "critical",
                )
                continue

            null_count = conn.execute(
                f'SELECT COUNT(*) FROM "{table_name}" '
                f'WHERE "{column_name}" IS NULL'
            ).fetchone()[0]

            add_check(
                f"null_{table_name}_{column_name}",
                f"NULL values in {table_name}.{column_name}.",
                null_count,
            )

    if "ActivityEvent" in table_counts:
        activity_columns = {
            row[1]
            for row in conn.execute(
                'PRAGMA table_info("ActivityEvent")'
            ).fetchall()
        }

        if "source_event_id" in activity_columns:
            duplicate_source_events = conn.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT source_event_id
                    FROM ActivityEvent
                    WHERE source_event_id IS NOT NULL
                    GROUP BY source_event_id
                    HAVING COUNT(*) > 1
                )
            """).fetchone()[0]

            add_check(
                "duplicate_source_event_ids",
                "Source event identifiers appearing more than once.",
                duplicate_source_events,
            )

    failed_checks = sum(
        check["status"] == "fail" for check in checks
    )

    return {
        "checks_run": len(checks),
        "failed_checks": failed_checks,
        "passed_checks": len(checks) - failed_checks,
        "foreign_key_violation_count": len(fk_violations),
        "checks": checks,
    }


def get_completion_metrics(conn):
    """Calculate current course completion metrics."""
    rows = conn.execute("""
        SELECT
            c.course_id,
            c.title AS course_title,
            COUNT(DISTINCT e.enrollment_id) AS total_enrollments,
            COUNT(DISTINCT CASE
                WHEN o.outcome_status = 'completed'
                THEN e.enrollment_id
            END) AS completed_enrollments,
            ROUND(
                100.0 * COUNT(DISTINCT CASE
                    WHEN o.outcome_status = 'completed'
                    THEN e.enrollment_id
                END) / NULLIF(COUNT(DISTINCT e.enrollment_id), 0),
                2
            ) AS completion_rate_pct,
            ROUND(AVG(o.completion_percentage), 2)
                AS avg_completion_percentage
        FROM Course c
        LEFT JOIN Enrollment e
            ON e.course_id = c.course_id
        LEFT JOIN CourseOutcome o
            ON o.enrollment_id = e.enrollment_id
           AND o.is_current = 1
        GROUP BY c.course_id, c.title
        ORDER BY c.title
    """).fetchall()

    columns = [
        "course_id",
        "course_title",
        "total_enrollments",
        "completed_enrollments",
        "completion_rate_pct",
        "avg_completion_percentage",
    ]

    return [dict(zip(columns, row)) for row in rows]


def get_assessment_metrics(conn):
    """Summarize graded assessment attempts and scores by course."""
    rows = conn.execute("""
        SELECT
            c.course_id,
            c.title AS course_title,
            COUNT(a.attempt_id) AS total_attempts,
            COUNT(a.score) AS scored_attempts,
            ROUND(AVG(a.score), 2) AS average_score,
            ROUND(MIN(a.score), 2) AS minimum_score,
            ROUND(MAX(a.score), 2) AS maximum_score,
            COUNT(CASE
                WHEN a.score >= ass.passing_score THEN 1
            END) AS passing_attempts,
            ROUND(
                100.0 * COUNT(CASE
                    WHEN a.score >= ass.passing_score THEN 1
                END) / NULLIF(COUNT(a.score), 0),
                2
            ) AS pass_rate_pct
        FROM Course c
        LEFT JOIN Assessment ass
            ON ass.course_id = c.course_id
        LEFT JOIN Attempt a
            ON a.assessment_id = ass.assessment_id
           AND a.status = 'graded'
        GROUP BY c.course_id, c.title
        ORDER BY c.title
    """).fetchall()

    columns = [
        "course_id",
        "course_title",
        "total_attempts",
        "scored_attempts",
        "average_score",
        "minimum_score",
        "maximum_score",
        "passing_attempts",
        "pass_rate_pct",
    ]

    return [dict(zip(columns, row)) for row in rows]


def get_engagement_metrics(conn):
    """Summarize activity events and active learners by course."""
    rows = conn.execute("""
        SELECT
            c.course_id,
            c.title AS course_title,
            COUNT(DISTINCT e.enrollment_id) AS total_enrollments,
            COUNT(DISTINCT CASE
                WHEN ae.event_id IS NOT NULL THEN e.learner_id
            END) AS active_learners,
            COUNT(ae.event_id) AS total_events,
            COUNT(DISTINCT ae.enrollment_id) AS active_enrollments,
            ROUND(
                1.0 * COUNT(ae.event_id)
                / NULLIF(COUNT(DISTINCT e.enrollment_id), 0),
                2
            ) AS events_per_enrollment
        FROM Course c
        LEFT JOIN Enrollment e
            ON e.course_id = c.course_id
        LEFT JOIN ActivityEvent ae
            ON ae.enrollment_id = e.enrollment_id
        GROUP BY c.course_id, c.title
        ORDER BY c.title
    """).fetchall()

    columns = [
        "course_id",
        "course_title",
        "total_enrollments",
        "active_learners",
        "total_events",
        "active_enrollments",
        "events_per_enrollment",
    ]

    return [dict(zip(columns, row)) for row in rows]


def get_anomaly_summary(database_path):
    """Run anomaly detection against the selected database."""
    from src.validation.anomaly_detector import detect_anomalies

    database_path = Path(database_path).resolve()

    previous_db_path = os.environ.get("LEARNING_ANALYTICS_DB")
    os.environ["LEARNING_ANALYTICS_DB"] = str(database_path)

    try:
        findings = detect_anomalies()
    finally:
        if previous_db_path is None:
            os.environ.pop("LEARNING_ANALYTICS_DB", None)
        else:
            os.environ["LEARNING_ANALYTICS_DB"] = previous_db_path

    issue_counts = Counter(
        finding["issue_type"] for finding in findings
    )

    return {
        "total_findings": len(findings),
        "status": (
            "clean" if not findings else "needs_investigation"
        ),
        "findings_by_type": dict(sorted(issue_counts.items())),
        "findings": findings,
    }


def build_report(database_path=None):
    """Build a report from an existing database without modifying it."""
    if database_path is None:
        database_path = os.environ.get(
            "LEARNING_ANALYTICS_DB",
            str(DEFAULT_DB_PATH),
        )

    database_path = Path(database_path).resolve()

    with closing(open_read_only_database(database_path)) as conn:
        table_counts = get_table_counts(conn)

        required_tables = {
            "Learner",
            "Course",
            "Enrollment",
            "ActivityEvent",
            "Assessment",
            "Attempt",
            "CourseOutcome",
        }

        missing_tables = sorted(
            required_tables - set(table_counts)
        )

        if missing_tables:
            raise RuntimeError(
                "Database is missing required tables: "
                + ", ".join(missing_tables)
            )

        quality = get_data_quality(conn, table_counts)
        completion = get_completion_metrics(conn)
        assessments = get_assessment_metrics(conn)
        engagement = get_engagement_metrics(conn)
        cohort_performance = get_cohort_performance(conn)
        inactive_enrollments = get_inactive_enrollment_metrics(conn)

        total_enrollments = table_counts.get("Enrollment", 0)

        completed_enrollments = conn.execute("""
            SELECT COUNT(*)
            FROM CourseOutcome
            WHERE is_current = 1
              AND outcome_status = 'completed'
        """).fetchone()[0]

        # Uses the same database path as the rest of the report.
        anomalies = get_anomaly_summary(database_path)

        report = {
            "report_metadata": {
                "generated_at_utc": datetime.now(
                    timezone.utc
                ).isoformat(),
                "database_path": str(database_path),
                "read_only": True,
            },
            "overview": {
                "learners": table_counts.get("Learner", 0),
                "courses": table_counts.get("Course", 0),
                "enrollments": total_enrollments,
                "completed_enrollments": completed_enrollments,
                "completion_rate_pct": (
                    round(
                        100.0 * completed_enrollments
                        / total_enrollments,
                        2,
                    )
                    if total_enrollments
                    else None
                ),
                "activity_events": table_counts.get(
                    "ActivityEvent", 0
                ),
                "assessment_attempts": table_counts.get(
                    "Attempt", 0
                ),
                "course_outcomes": table_counts.get(
                    "CourseOutcome", 0
                ),
            },
            "data_quality": quality,
            "anomaly_detection": anomalies,
            "course_completion": completion,
            "assessment_performance": assessments,
            "learner_engagement": engagement,
            "cohort_performance": cohort_performance,
            "inactive_enrollments": inactive_enrollments,
        }

    return report


def write_report(report, output_path=None):
    """Write a JSON report without overwriting an existing file."""
    if output_path is None:
        output_path = DEFAULT_REPORT_PATH

    output_path = Path(output_path).resolve()

    if output_path.exists():
        raise FileExistsError(
            f"Report already exists: {output_path}. "
            "Choose a new output filename."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Exclusive creation prevents accidental overwrites.
    with output_path.open("x", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(f"Report saved to: {output_path}")
    return output_path


def main():
    database_path = os.environ.get(
        "LEARNING_ANALYTICS_DB",
        str(DEFAULT_DB_PATH),
    )

    report = build_report(database_path)

    # Use a new filename so the existing report is preserved.
    output_path = (
        PROJECT_ROOT
        / "reports"
        / "learning_analytics_report_with_anomalies.json"
    )

    write_report(report, output_path)

    print("\nREPORT OVERVIEW")
    print("=" * 40)

    for metric, value in report["overview"].items():
        print(f"{metric}: {value}")

    print("\nDATA QUALITY")
    print("=" * 40)
    print(f"Checks run: {report['data_quality']['checks_run']}")
    print(f"Passed: {report['data_quality']['passed_checks']}")
    print(f"Failed: {report['data_quality']['failed_checks']}")

    print("\nANOMALY DETECTION")
    print("=" * 40)
    print(
        "Status: "
        f"{report['anomaly_detection']['status']}"
    )
    print(
        "Total findings: "
        f"{report['anomaly_detection']['total_findings']}"
    )

    for issue_type, count in (
        report["anomaly_detection"]["findings_by_type"].items()
    ):
        print(f"{issue_type}: {count}")


if __name__ == "__main__":
    main()
