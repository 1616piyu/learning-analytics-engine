
import os
import random
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path

from faker import Faker

from src.generator.config import REFERENCE_TIME, SEED

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def generate_master_data(
    learner_count=100,
    course_count=10,
    cohort_count=4,
):
    database_path = Path(
        os.environ.get(
            "LEARNING_ANALYTICS_DB",
            str(PROJECT_ROOT / "data" / "learning_analytics.db"),
        )
    )

    rng = random.Random(SEED)
    fake = Faker()
    fake.seed_instance(SEED)
    now = REFERENCE_TIME

    with closing(sqlite3.connect(database_path)) as conn:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")

            learners = []
            for i in range(1, learner_count + 1):
                learners.append((
                    f"LRN-{i:06d}",
                    fake.name(),
                    f"learner{i:06d}@example.test",
                    (now - timedelta(days=rng.randint(0, 730))).isoformat(),
                    rng.choices(
                        ["active", "inactive", "suspended"],
                        weights=[80, 15, 5],
                    )[0],
                ))

            conn.executemany(
                """
                INSERT INTO Learner
                    (learner_id, name, email, created_at, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                learners,
            )

            categories = [
                "Artificial Intelligence",
                "Data Science",
                "Python",
                "Cloud Computing",
                "Machine Learning",
            ]

            courses = []
            for i in range(1, course_count + 1):
                courses.append((
                    f"CRS-{i:06d}",
                    f"{fake.catch_phrase()} Course {i}",
                    rng.choice(categories),
                    "published",
                    (now - timedelta(days=rng.randint(30, 365))).isoformat(),
                ))

            conn.executemany(
                """
                INSERT INTO Course
                    (course_id, title, category, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                courses,
            )

            cohorts = []
            for i in range(1, cohort_count + 1):
                start_date = now.date() - timedelta(days=30 * i)
                cohorts.append((
                    f"COH-{i:04d}",
                    f"Cohort {i}",
                    start_date.isoformat(),
                    None,
                    f"Synthetic learner cohort {i}",
                ))

            conn.executemany(
                """
                INSERT INTO Cohort
                    (cohort_id, name, start_date, end_date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                cohorts,
            )

    print(f"Generated {learner_count:,} learners")
    print(f"Generated {course_count:,} courses")
    print(f"Generated {cohort_count:,} cohorts")


if __name__ == "__main__":
    generate_master_data()
