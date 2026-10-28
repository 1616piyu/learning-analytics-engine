
import os
import random
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from src.generator.config import REFERENCE_TIME, SEED


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = Path(
    os.environ.get(
        "LEARNING_ANALYTICS_DB",
        str(PROJECT_ROOT / "data" / "learning_analytics.db"),
    )
)


def generate_activity_data():
    rng = random.Random(SEED)
    now = REFERENCE_TIME

    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        # Enable foreign-key enforcement before starting the transaction.
        conn.execute("PRAGMA foreign_keys = ON")

        # Keep ALL reads, generation and writes in one transaction.
        with conn:
            enrollments = conn.execute("""
                SELECT enrollment_id, course_id, enrolled_at
                FROM Enrollment
                ORDER BY enrollment_id
            """).fetchall()

            content = conn.execute("""
                SELECT content_id, course_id, content_type
                FROM ContentItem
                WHERE is_required = 1
                ORDER BY content_id
            """).fetchall()

            assessments = conn.execute("""
                SELECT assessment_id, course_id, passing_score
                FROM Assessment
                ORDER BY assessment_id
            """).fetchall()

            content_by_course = {}
            for content_id, course_id, content_type in content:
                content_by_course.setdefault(course_id, []).append(
                    (content_id, content_type)
                )

            assessment_by_course = {
                course_id: (assessment_id, passing_score)
                for assessment_id, course_id, passing_score in assessments
            }

            events = []
            attempts = []
            event_counter = {}
            attempt_counter = 0

            for enrollment_id, course_id, enrolled_at in enrollments:
                enrollment_date = datetime.fromisoformat(enrolled_at)

                if enrollment_date.tzinfo is None:
                    raise ValueError(
                        f"Enrollment {enrollment_id} has a "
                        "timezone-naive timestamp"
                    )

                # Some learners are inactive and generate no activity.
                if rng.random() < 0.15:
                    continue

                course_content = content_by_course.get(course_id, [])

                # Generate activity for required content items.
                for content_id, content_type in course_content:
                    if rng.random() < 0.70:
                        event_counter[enrollment_id] = (
                            event_counter.get(enrollment_id, 0) + 1
                        )

                        event_time = enrollment_date + timedelta(
                            days=rng.randint(0, 30),
                            hours=rng.randint(0, 23),
                        )
                        event_time = min(event_time, now)

                        ingested_at = min(
                            event_time
                            + timedelta(minutes=rng.randint(0, 120)),
                            now,
                        )

                        events.append((
                            f"EVT-{enrollment_id}-"
                            f"{event_counter[enrollment_id]:06d}",
                            enrollment_id,
                            content_id,
                            "content_completed",
                            event_time.isoformat(),
                            ingested_at.isoformat(),
                            None,
                            rng.choice(["web", "mobile", "offline_sync"]),
                            None,
                        ))

                # Generate 0–3 assessment attempts per eligible enrollment.
                assessment_info = assessment_by_course.get(course_id)
                if assessment_info is None:
                    continue

                assessment_id, passing_score = assessment_info
                number_of_attempts = rng.randint(0, 3)

                for attempt_number in range(1, number_of_attempts + 1):
                    attempt_counter += 1

                    started_at = enrollment_date + timedelta(
                        days=rng.randint(1, 40)
                    )
                    started_at = min(
                        started_at,
                        now - timedelta(minutes=30),
                    )

                    score = round(rng.uniform(30, 100), 2)

                    attempts.append((
                        f"ATT-{attempt_counter:08d}",
                        enrollment_id,
                        assessment_id,
                        attempt_number,
                        score,
                        started_at.isoformat(),
                        (started_at + timedelta(minutes=30)).isoformat(),
                        "graded",
                    ))

            # Both inserts are inside the transaction.
            conn.executemany("""
                INSERT INTO ActivityEvent (
                    event_id,
                    enrollment_id,
                    content_id,
                    event_type,
                    event_time,
                    ingested_at,
                    source_event_id,
                    device_type,
                    issue_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, events)

            conn.executemany("""
                INSERT INTO Attempt (
                    attempt_id,
                    enrollment_id,
                    assessment_id,
                    attempt_number,
                    score,
                    started_at,
                    submitted_at,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, attempts)

    # Print counts only after the transaction has committed and the
    # connection has closed successfully.
    print(f"Generated {len(events)} activity events")
    print(f"Generated {len(attempts)} assessment attempts")


if __name__ == "__main__":
    generate_activity_data()
