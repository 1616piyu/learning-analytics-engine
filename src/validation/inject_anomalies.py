
import os
import csv
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = Path(
    os.environ.get(
        "LEARNING_ANALYTICS_DB",
        str(PROJECT_ROOT / "data" / "anomaly_test.db"),
    )
)

GROUND_TRUTH_PATH = Path(
    os.environ.get(
        "LEARNING_ANALYTICS_GROUND_TRUTH",
        str(PROJECT_ROOT / "data" / "ground_truth" / "ground_truth.csv"),
    )
)

INJECTION_TIME = datetime(
    2026, 10, 27, 12, 0, tzinfo=timezone.utc
)


def inject_anomalies():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}\n"
            "Build the pipeline first."
        )

    ground_truth = []

    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # 1. Select a valid enrollment and content item.
            enrollment = conn.execute("""
                SELECT e.enrollment_id, e.course_id
                FROM Enrollment e
                ORDER BY e.enrollment_id
                LIMIT 1
            """).fetchone()

            if not enrollment:
                raise RuntimeError(
                    "No enrollments found. Generate enrollments first."
                )

            enrollment_id, course_id = enrollment

            content_row = conn.execute("""
                SELECT content_id
                FROM ContentItem
                WHERE course_id = ?
                ORDER BY content_id
                LIMIT 1
            """, (course_id,)).fetchone()

            if not content_row:
                raise RuntimeError(
                    f"No content found for course {course_id}"
                )

            content_id = content_row[0]

            # 2. Duplicate activity events.
            now = INJECTION_TIME
            base_time = now - timedelta(hours=2)

            duplicate_rows = [
                (
                    "EVT-ANOMALY-DUP-000001",
                    enrollment_id,
                    content_id,
                    "content_opened",
                    base_time.isoformat(),
                    now.isoformat(),
                    "SOURCE-DUP-001",
                    "mobile",
                    "duplicate_event",
                ),
                (
                    "EVT-ANOMALY-DUP-000002",
                    enrollment_id,
                    content_id,
                    "content_opened",
                    base_time.isoformat(),
                    now.isoformat(),
                    "SOURCE-DUP-001",
                    "mobile",
                    "duplicate_event",
                ),
            ]

            conn.executemany("""
                INSERT OR IGNORE INTO ActivityEvent (
                    event_id, enrollment_id, content_id, event_type,
                    event_time, ingested_at, source_event_id,
                    device_type, issue_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, duplicate_rows)

            ground_truth.extend([
                (
                    "EVT-ANOMALY-DUP-000001",
                    "duplicate_event",
                    "duplicate",
                ),
                (
                    "EVT-ANOMALY-DUP-000002",
                    "duplicate_event",
                    "duplicate",
                ),
            ])

            # 3. Activity event without an enrollment link.
            invalid_event_id = "EVT-ANOMALY-UNENROLLED-000001"

            conn.execute("""
                INSERT OR IGNORE INTO ActivityEvent (
                    event_id, enrollment_id, content_id, event_type,
                    event_time, ingested_at, source_event_id,
                    device_type, issue_type
                )
                VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invalid_event_id,
                content_id,
                "content_opened",
                now.isoformat(),
                now.isoformat(),
                "SOURCE-UNENROLLED-001",
                "web",
                "unenrolled_activity",
            ))

            ground_truth.append((
                invalid_event_id,
                "unenrolled_activity",
                "invalid",
            ))

            # 4. Completion without a passing required assessment.
            candidate = conn.execute("""
                SELECT
                    e.enrollment_id,
                    e.course_id,
                    cr.rule_id
                FROM Enrollment e
                JOIN CompletionRule cr
                    ON cr.course_id = e.course_id
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM Assessment a
                    JOIN Attempt at
                        ON at.assessment_id = a.assessment_id
                       AND at.enrollment_id = e.enrollment_id
                    WHERE a.course_id = e.course_id
                      AND a.is_required = 1
                      AND at.status = 'graded'
                      AND at.score >= a.passing_score
                )
                ORDER BY e.enrollment_id, cr.rule_version DESC
                LIMIT 1
            """).fetchone()

            if not candidate:
                raise RuntimeError(
                    "Could not find an enrollment without a passing "
                    "required assessment. Cannot create a reliable "
                    "completion anomaly."
                )

            completion_enrollment_id, completion_course_id, rule_id = (
                candidate
            )

            outcome_id = "OUT-ANOMALY-000001"

            conn.execute("""
                INSERT OR IGNORE INTO CourseOutcome (
                    outcome_id, enrollment_id, calculated_at,
                    outcome_status, completion_percentage,
                    rule_id, is_current
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome_id,
                completion_enrollment_id,
                now.isoformat(),
                "completed",
                100.0,
                rule_id,
                0,
            ))

            ground_truth.append((
                outcome_id,
                "completion_before_assessment",
                "invalid",
            ))

            # 5. Timezone-boundary event.
            timezone_event_id = "EVT-ANOMALY-TZ-000001"
            local_time = "2026-10-25T00:30:00+05:30"

            utc_time = datetime.fromisoformat(
                local_time
            ).astimezone(timezone.utc)

            conn.execute("""
                INSERT OR IGNORE INTO ActivityEvent (
                    event_id, enrollment_id, content_id, event_type,
                    event_time, ingested_at, source_event_id,
                    device_type, issue_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timezone_event_id,
                enrollment_id,
                content_id,
                "content_opened",
                local_time,
                utc_time.isoformat(),
                "SOURCE-TZ-001",
                "mobile",
                "timezone_boundary",
            ))

            ground_truth.append((
                timezone_event_id,
                "timezone_boundary",
                "review",
            ))

    # 6. Write ground truth to a separate CSV file.
    GROUND_TRUTH_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with GROUND_TRUTH_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "record_id",
            "issue_type",
            "expected_decision",
        ])
        writer.writerows(ground_truth)

    print(f"Database used: {DATABASE_PATH}")
    print(f"Ground truth written to: {GROUND_TRUTH_PATH}")
    print(f"Labelled test cases: {len(ground_truth)}")


if __name__ == "__main__":
    inject_anomalies()
