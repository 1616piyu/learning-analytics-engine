
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = Path(
    os.environ.get(
        "LEARNING_ANALYTICS_DB",
        str(PROJECT_ROOT / "data" / "learning_analytics.db"),
    )
)


def detect_anomalies(database_path=None):
    """
    Detect known data-quality anomalies in a SQLite database.

    Args:
        database_path: Optional path to the database. If omitted,
            use LEARNING_ANALYTICS_DB when set, otherwise DB_PATH.

    Returns:
        A list of findings with record, issue_type, and details.
    """
    if database_path is None:
        database_path = os.environ.get(
            "LEARNING_ANALYTICS_DB",
            str(DB_PATH),
        )

    database_path = Path(database_path).resolve()

    if not database_path.is_file():
        raise FileNotFoundError(
            f"Database not found: {database_path}"
        )

    findings = []

    with closing(sqlite3.connect(database_path)) as conn:
        # 1. Detect duplicate activity events by source event identity.
        duplicate_groups = conn.execute("""
            SELECT
                source_event_id,
                enrollment_id,
                content_id,
                event_type
            FROM ActivityEvent
            WHERE source_event_id IS NOT NULL
            GROUP BY
                source_event_id,
                enrollment_id,
                content_id,
                event_type
            HAVING COUNT(*) > 1
        """).fetchall()

        for (
            source_id,
            enrollment_id,
            content_id,
            event_type,
        ) in duplicate_groups:
            rows = conn.execute("""
                SELECT event_id
                FROM ActivityEvent
                WHERE source_event_id = ?
                  AND enrollment_id IS ?
                  AND content_id IS ?
                  AND event_type = ?
                ORDER BY event_id
            """, (
                source_id,
                enrollment_id,
                content_id,
                event_type,
            )).fetchall()

            for (event_id,) in rows:
                findings.append({
                    "record": event_id,
                    "issue_type": "duplicate_event",
                    "details": f"Duplicate source event: {source_id}",
                })

        # 2. Detect events without a valid enrollment.
        rows = conn.execute("""
            SELECT e.event_id
            FROM ActivityEvent e
            LEFT JOIN Enrollment en
                ON e.enrollment_id = en.enrollment_id
            WHERE e.enrollment_id IS NULL
               OR en.enrollment_id IS NULL
            ORDER BY e.event_id
        """).fetchall()

        for (event_id,) in rows:
            findings.append({
                "record": event_id,
                "issue_type": "unenrolled_activity",
                "details": "Event has no valid enrollment",
            })

        # 3. Detect completed outcomes without a passing required assessment.
        rows = conn.execute("""
            SELECT o.outcome_id
            FROM CourseOutcome o
            JOIN Enrollment en
                ON o.enrollment_id = en.enrollment_id
            JOIN CompletionRule cr
                ON o.rule_id = cr.rule_id
            WHERE o.outcome_status = 'completed'
              AND cr.require_assessment_pass = 1
              AND EXISTS (
                  SELECT 1
                  FROM Assessment required_assessment
                  WHERE required_assessment.course_id = en.course_id
                    AND required_assessment.is_required = 1
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM Attempt a
                  JOIN Assessment ass
                    ON a.assessment_id = ass.assessment_id
                  WHERE a.enrollment_id = en.enrollment_id
                    AND ass.course_id = en.course_id
                    AND ass.is_required = 1
                    AND a.status = 'graded'
                    AND a.score IS NOT NULL
                    AND a.score >= ass.passing_score
              )
            ORDER BY o.outcome_id
        """).fetchall()

        for (outcome_id,) in rows:
            findings.append({
                "record": outcome_id,
                "issue_type": "completion_before_assessment",
                "details": (
                    "Completed outcome has no passing attempt "
                    "for a required assessment"
                ),
            })

        # 4. Detect timezone-boundary events from timestamp values.
        rows = conn.execute("""
            SELECT event_id, event_time
            FROM ActivityEvent
            WHERE event_time IS NOT NULL
            ORDER BY event_id
        """).fetchall()

        for event_id, event_time in rows:
            try:
                parsed = datetime.fromisoformat(
                    event_time.replace("Z", "+00:00")
                )

                if parsed.tzinfo is None:
                    continue

                utc_time = parsed.astimezone(timezone.utc)

                if parsed.date() != utc_time.date():
                    findings.append({
                        "record": event_id,
                        "issue_type": "timezone_boundary",
                        "details": "Local date differs from UTC date",
                    })

            except (ValueError, TypeError):
                continue

    return findings


if __name__ == "__main__":
    findings = detect_anomalies()

    print("\nANOMALY DETECTION REPORT")
    print("=" * 45)

    for item in findings:
        print(
            f"{item['issue_type']}: {item['record']} - "
            f"{item['details']}"
        )

    print(f"\nTotal anomaly findings: {len(findings)}")
