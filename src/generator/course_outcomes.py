
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from src.generator.config import REFERENCE_TIME


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = Path(
    os.environ.get(
        "LEARNING_ANALYTICS_DB",
        str(PROJECT_ROOT / "data" / "learning_analytics.db"),
    )
)


def generate_course_outcomes():
    """
    Calculate course outcomes from completed content and graded
    assessment attempts.

    Re-running the generator updates existing current outcomes.
    Historical, non-current outcomes are preserved.
    """
    generated = 0
    inserted = 0
    updated = 0

    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")

            calculated_at = REFERENCE_TIME.isoformat()

            enrollments = conn.execute(
                """
                SELECT
                    en.enrollment_id,
                    en.course_id,
                    cr.rule_id,
                    cr.required_content_count,
                    cr.require_assessment_pass
                FROM Enrollment en
                JOIN CompletionRule cr
                    ON cr.course_id = en.course_id
                WHERE cr.effective_from <= ?
                  AND (
                      cr.effective_to IS NULL
                      OR cr.effective_to >= ?
                  )
                """,
                (calculated_at, calculated_at),
            ).fetchall()

            for (
                enrollment_id,
                course_id,
                rule_id,
                required_content_count,
                require_assessment_pass,
            ) in enrollments:

                completed_content = conn.execute(
                    """
                    SELECT COUNT(DISTINCT ci.content_id)
                    FROM ActivityEvent e
                    JOIN ContentItem ci
                        ON ci.content_id = e.content_id
                    WHERE e.enrollment_id = ?
                      AND ci.course_id = ?
                      AND ci.is_required = 1
                      AND e.event_type = 'content_completed'
                    """,
                    (enrollment_id, course_id),
                ).fetchone()[0]

                content_target = max(required_content_count, 0)

                if content_target == 0:
                    content_percentage = 100.0
                else:
                    content_percentage = min(
                        100.0,
                        100.0 * completed_content / content_target,
                    )

                passed_assessment = conn.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM Attempt a
                        JOIN Assessment ass
                            ON ass.assessment_id = a.assessment_id
                        WHERE a.enrollment_id = ?
                          AND ass.course_id = ?
                          AND ass.is_required = 1
                          AND a.status = 'graded'
                          AND a.score IS NOT NULL
                          AND a.score >= ass.passing_score
                    )
                    """,
                    (enrollment_id, course_id),
                ).fetchone()[0]

                content_complete = (
                    completed_content >= content_target
                )

                assessment_complete = (
                    not require_assessment_pass
                    or bool(passed_assessment)
                )

                is_complete = (
                    content_complete and assessment_complete
                )

                outcome_status = (
                    "completed" if is_complete else "in_progress"
                )

                completion_percentage = content_percentage

                if (
                    require_assessment_pass
                    and not passed_assessment
                ):
                    completion_percentage = min(
                        completion_percentage, 99.0
                    )

                completion_percentage = round(
                    completion_percentage, 2
                )

                existing = conn.execute(
                    """
                    SELECT outcome_id
                    FROM CourseOutcome
                    WHERE enrollment_id = ?
                      AND is_current = 1
                    ORDER BY calculated_at DESC
                    LIMIT 1
                    """,
                    (enrollment_id,),
                ).fetchone()

                if existing:
                    conn.execute(
                        """
                        UPDATE CourseOutcome
                        SET calculated_at = ?,
                            outcome_status = ?,
                            completion_percentage = ?,
                            rule_id = ?
                        WHERE outcome_id = ?
                        """,
                        (
                            calculated_at,
                            outcome_status,
                            completion_percentage,
                            rule_id,
                            existing[0],
                        ),
                    )
                    updated += 1

                else:
                    outcome_id = (
                        f"OUT-{enrollment_id}-{rule_id}"
                    )

                    collision = conn.execute(
                        """
                        SELECT 1
                        FROM CourseOutcome
                        WHERE outcome_id = ?
                        """,
                        (outcome_id,),
                    ).fetchone()

                    if collision:
                        outcome_id = (
                            f"{outcome_id}-"
                            f"{calculated_at.replace(':', '-')}"
                        )

                    conn.execute(
                        """
                        INSERT INTO CourseOutcome (
                            outcome_id,
                            enrollment_id,
                            calculated_at,
                            outcome_status,
                            completion_percentage,
                            rule_id,
                            is_current
                        )
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            outcome_id,
                            enrollment_id,
                            calculated_at,
                            outcome_status,
                            completion_percentage,
                            rule_id,
                        ),
                    )
                    inserted += 1

                generated += 1

    print("COURSE OUTCOME GENERATION")
    print("=" * 35)
    print(f"Eligible enrollments processed: {generated}")
    print(f"Current outcomes inserted:      {inserted}")
    print(f"Current outcomes updated:       {updated}")


if __name__ == "__main__":
    generate_course_outcomes()
