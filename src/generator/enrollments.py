
import os
import random
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path

from src.generator.config import REFERENCE_TIME, SEED


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = Path(
    os.environ.get(
        "LEARNING_ANALYTICS_DB",
        str(PROJECT_ROOT / "data" / "learning_analytics.db"),
    )
)


def generate_enrollments(
    min_courses_per_learner=3,
    max_courses_per_learner=5,
):
    rng = random.Random(SEED)
    now = REFERENCE_TIME

    enrollments = []
    learner_cohorts = []

    # Explicitly close the connection after the transaction.
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")

            learners = conn.execute(
                """
                SELECT learner_id
                FROM Learner
                ORDER BY learner_id
                """
            ).fetchall()

            courses = conn.execute(
                """
                SELECT course_id
                FROM Course
                ORDER BY course_id
                """
            ).fetchall()

            cohorts = conn.execute(
                """
                SELECT cohort_id, start_date
                FROM Cohort
                ORDER BY cohort_id
                """
            ).fetchall()

            learner_ids = [row[0] for row in learners]
            course_ids = [row[0] for row in courses]

            if len(course_ids) < min_courses_per_learner:
                raise ValueError(
                    "Not enough courses for requested enrollment range"
                )

            if not cohorts and learner_ids:
                raise ValueError(
                    "No cohorts available for learner assignment"
                )

            # Generate learner-cohort memberships and enrollments.
            for learner_id in learner_ids:
                cohort_id, cohort_start = rng.choice(cohorts)

                learner_cohorts.append((
                    learner_id,
                    cohort_id,
                    cohort_start + "T00:00:00+00:00",
                    None,
                ))

                course_count = rng.randint(
                    min_courses_per_learner,
                    min(max_courses_per_learner, len(course_ids)),
                )

                selected_courses = rng.sample(
                    course_ids,
                    course_count,
                )

                for course_id in selected_courses:
                    enrollment_id = (
                        f"ENR-{learner_id}-{course_id}"
                    )

                    enrolled_at = now - timedelta(
                        days=rng.randint(1, 180)
                    )

                    status = rng.choices(
                        [
                            "enrolled",
                            "in_progress",
                            "completed",
                            "withdrawn",
                        ],
                        weights=[15, 45, 30, 10],
                    )[0]

                    enrollments.append((
                        enrollment_id,
                        learner_id,
                        course_id,
                        enrolled_at.isoformat(),
                        status,
                    ))

            # Insert learner-cohort memberships.
            conn.executemany(
                """
                INSERT INTO LearnerCohort (
                    learner_id,
                    cohort_id,
                    joined_at,
                    left_at
                )
                VALUES (?, ?, ?, ?)
                """,
                learner_cohorts,
            )

            # Insert course enrollments.
            conn.executemany(
                """
                INSERT INTO Enrollment (
                    enrollment_id,
                    learner_id,
                    course_id,
                    enrolled_at,
                    status
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                enrollments,
            )

    print(f"Generated {len(enrollments)} enrollments")
    print(
        f"Assigned {len(learner_cohorts)} "
        f"learner-cohort memberships"
    )


if __name__ == "__main__":
    generate_enrollments()
