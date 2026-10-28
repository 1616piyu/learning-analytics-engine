
import os
import random
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path

from src.generator.config import REFERENCE_TIME, SEED

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def generate_enrollments(
    min_courses_per_learner=3,
    max_courses_per_learner=5,
    target_enrollment_count=None,
):
    database_path = Path(
        os.environ.get(
            "LEARNING_ANALYTICS_DB",
            str(PROJECT_ROOT / "data" / "learning_analytics.db"),
        )
    )

    rng = random.Random(SEED)
    now = REFERENCE_TIME

    with closing(sqlite3.connect(database_path)) as conn:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")

            learner_ids = [
                row[0] for row in conn.execute(
                    "SELECT learner_id FROM Learner ORDER BY learner_id"
                )
            ]
            course_ids = [
                row[0] for row in conn.execute(
                    "SELECT course_id FROM Course ORDER BY course_id"
                )
            ]
            cohorts = conn.execute(
                "SELECT cohort_id, start_date FROM Cohort ORDER BY cohort_id"
            ).fetchall()

            if learner_ids and not cohorts:
                raise ValueError("No cohorts available for learner assignment")
            if not course_ids:
                raise ValueError("No courses available for enrollment")

            if target_enrollment_count is not None:
                if target_enrollment_count > len(learner_ids) * len(course_ids):
                    raise ValueError(
                        "Requested enrollments exceed unique learner-course pairs"
                    )
                if target_enrollment_count < len(learner_ids):
                    raise ValueError(
                        "Target must allow at least one enrollment per learner"
                    )

                # Five courses per learner gives 100,000 for the full profile.
                if target_enrollment_count % len(learner_ids) != 0:
                    raise ValueError(
                        "For deterministic balanced allocation, target enrollments "
                        "must be divisible by learner count"
                    )

                courses_per_learner = target_enrollment_count // len(learner_ids)
                if courses_per_learner > len(course_ids):
                    raise ValueError("Not enough distinct courses per learner")
                min_per_learner = max_per_learner = courses_per_learner
            else:
                min_per_learner = min_courses_per_learner
                max_per_learner = min(max_courses_per_learner, len(course_ids))

            memberships = []
            enrollments = []

            for learner_id in learner_ids:
                cohort_id, cohort_start = rng.choice(cohorts)
                memberships.append((
                    learner_id,
                    cohort_id,
                    cohort_start + "T00:00:00+00:00",
                    None,
                ))

                count = rng.randint(min_per_learner, max_per_learner)
                selected_courses = rng.sample(course_ids, count)

                for course_id in selected_courses:
                    enrolled_at = now - timedelta(days=rng.randint(1, 180))
                    status = rng.choices(
                        ["enrolled", "in_progress", "completed", "withdrawn"],
                        weights=[15, 45, 30, 10],
                    )[0]

                    enrollments.append((
                        f"ENR-{learner_id}-{course_id}",
                        learner_id,
                        course_id,
                        enrolled_at.isoformat(),
                        status,
                    ))

            conn.executemany(
                """
                INSERT INTO LearnerCohort
                    (learner_id, cohort_id, joined_at, left_at)
                VALUES (?, ?, ?, ?)
                """,
                memberships,
            )
            conn.executemany(
                """
                INSERT INTO Enrollment
                    (enrollment_id, learner_id, course_id, enrolled_at, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                enrollments,
            )

    print(f"Generated {len(enrollments):,} enrollments")
    print(f"Assigned {len(memberships):,} learner-cohort memberships")


if __name__ == "__main__":
    generate_enrollments()
