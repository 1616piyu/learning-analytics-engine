
import os
import sqlite3
from contextlib import closing
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = Path(
    os.environ.get(
        "LEARNING_ANALYTICS_DB",
        str(PROJECT_ROOT / "data" / "learning_analytics.db"),
    )
)


def validate_database():
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        checks = {
            "Duplicate learner IDs": """
                SELECT COUNT(*) FROM (
                    SELECT learner_id
                    FROM Learner
                    GROUP BY learner_id
                    HAVING COUNT(*) > 1
                )
            """,
            "Invalid enrollment references": """
                SELECT COUNT(*)
                FROM Enrollment e
                LEFT JOIN Learner l
                    ON e.learner_id = l.learner_id
                LEFT JOIN Course c
                    ON e.course_id = c.course_id
                WHERE l.learner_id IS NULL
                   OR c.course_id IS NULL
            """,
            "Events without a valid enrollment": """
                SELECT COUNT(*)
                FROM ActivityEvent a
                LEFT JOIN Enrollment e
                    ON a.enrollment_id = e.enrollment_id
                WHERE a.enrollment_id IS NULL
                   OR e.enrollment_id IS NULL
            """,
            "Attempts with mismatched courses": """
                SELECT COUNT(*)
                FROM Attempt a
                JOIN Enrollment e
                    ON a.enrollment_id = e.enrollment_id
                JOIN Assessment s
                    ON a.assessment_id = s.assessment_id
                WHERE e.course_id != s.course_id
            """,
            "Content with mismatched courses": """
                SELECT COUNT(*)
                FROM ContentItem child
                JOIN ContentItem parent
                    ON child.parent_content_id = parent.content_id
                WHERE child.course_id != parent.course_id
            """,
            "Invalid attempt date ordering": """
                SELECT COUNT(*)
                FROM Attempt
                WHERE submitted_at IS NOT NULL
                  AND submitted_at < started_at
            """,
            "Events ingested before they occurred": """
                SELECT COUNT(*)
                FROM ActivityEvent
                WHERE julianday(ingested_at) < julianday(event_time)
            """,
            "Duplicate current outcomes": """
                SELECT COUNT(*) FROM (
                    SELECT enrollment_id
                    FROM CourseOutcome
                    WHERE is_current = 1
                    GROUP BY enrollment_id
                    HAVING COUNT(*) > 1
                )
            """,
            "Outcomes with mismatched course rules": """
                SELECT COUNT(*)
                FROM CourseOutcome o
                JOIN Enrollment e
                    ON e.enrollment_id = o.enrollment_id
                JOIN CompletionRule r
                    ON r.rule_id = o.rule_id
                WHERE e.course_id != r.course_id
            """,
            "Invalid completion percentages": """
                SELECT COUNT(*)
                FROM CourseOutcome
                WHERE completion_percentage < 0
                   OR completion_percentage > 100
            """,
        }

        print("\nDATA VALIDATION REPORT")
        print("=" * 55)
        print(f"Database: {DATABASE_PATH}\n")

        failed = False

        for name, query in checks.items():
            count = conn.execute(query).fetchone()[0]
            status = "PASS" if count == 0 else "FAIL"
            print(f"{status}: {name} = {count}")

            if count:
                failed = True

        fk_errors = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        print(
            f"{'PASS' if not fk_errors else 'FAIL'}: "
            f"Foreign key check = {len(fk_errors)} violations"
        )

        if fk_errors:
            failed = True

    return not failed


if __name__ == "__main__":
    success = validate_database()

    if not success:
        raise SystemExit(
            "Validation failed. Investigate the reported issues."
        )

    print("\nAll integrity checks passed.")
