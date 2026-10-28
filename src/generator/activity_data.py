
import os
import random
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from src.generator.config import REFERENCE_TIME, SEED

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BATCH_SIZE = 10_000


def generate_activity_data(target_event_count=None):
    """
    Generate activity events and assessment attempts.

    target_event_count=None preserves the original starter behavior.
    Supplying a target generates exactly that many events, provided the
    natural generation does not already exceed the target.
    """
    database_path = Path(
        os.environ.get(
            "LEARNING_ANALYTICS_DB",
            str(PROJECT_ROOT / "data" / "learning_analytics.db"),
        )
    )

    rng = random.Random(SEED)
    now = REFERENCE_TIME

    with closing(sqlite3.connect(database_path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

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

            # Original natural event and attempt generation.
            # Keep this sequence unchanged for starter reproducibility.
            for enrollment_id, course_id, enrolled_at in enrollments:
                enrollment_date = datetime.fromisoformat(enrolled_at)

                if enrollment_date.tzinfo is None:
                    raise ValueError(
                        f"Enrollment {enrollment_id} has a "
                        "timezone-naive timestamp"
                    )

                if rng.random() < 0.15:
                    continue

                course_content = content_by_course.get(course_id, [])

                for content_id, _content_type in course_content:
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

                assessment_info = assessment_by_course.get(course_id)
                if assessment_info is None:
                    continue

                assessment_id, _passing_score = assessment_info
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

            if target_event_count is not None:
                if target_event_count < 0:
                    raise ValueError("target_event_count cannot be negative")

                if len(events) > target_event_count:
                    raise ValueError(
                        f"Natural generation produced {len(events):,} events, "
                        f"more than target {target_event_count:,}. "
                        "Increase the target."
                    )

                if target_event_count > len(events) and not enrollments:
                    raise ValueError(
                        "Cannot generate target events without enrollments"
                    )

            # Insert the original events and attempts.
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
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, attempts)

            natural_event_count = len(events)

            # Optional full-scale top-up.
            # Starter mode skips this entire block, preserving its original
            # generated event and attempt counts.
            if (
                target_event_count is not None
                and natural_event_count < target_event_count
            ):
                enrollment_lookup = []

                for enrollment_id, course_id, enrolled_at in enrollments:
                    course_content = content_by_course.get(course_id, [])
                    if course_content:
                        enrollment_lookup.append((
                            enrollment_id,
                            datetime.fromisoformat(enrolled_at),
                            course_content,
                        ))

                if not enrollment_lookup:
                    raise ValueError(
                        "No enrollment has required content for top-up events"
                    )

                event_types = [
                    "content_opened",
                    "content_completed",
                    "video_progress",
                    "assessment_started",
                    "assessment_submitted",
                ]

                batch = []
                generated = natural_event_count

                while generated < target_event_count:
                    enrollment_id, enrollment_date, course_content = (
                        rng.choice(enrollment_lookup)
                    )
                    content_id, _content_type = rng.choice(course_content)

                    event_counter[enrollment_id] = (
                        event_counter.get(enrollment_id, 0) + 1
                    )

                    event_time = min(
                        enrollment_date + timedelta(
                            minutes=rng.randint(0, 60 * 24 * 180)
                        ),
                        now,
                    )

                    ingested_at = min(
                        event_time + timedelta(
                            minutes=rng.randint(0, 120)
                        ),
                        now,
                    )

                    batch.append((
                        f"EVT-{enrollment_id}-"
                        f"{event_counter[enrollment_id]:06d}",
                        enrollment_id,
                        content_id,
                        rng.choice(event_types),
                        event_time.isoformat(),
                        ingested_at.isoformat(),
                        None,
                        rng.choice(["web", "mobile", "offline_sync"]),
                        None,
                    ))

                    generated += 1

                    if len(batch) >= BATCH_SIZE:
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
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, batch)
                        batch.clear()

                if batch:
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
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch)

    final_event_count = (
        target_event_count
        if target_event_count is not None
        else natural_event_count
    )

    print(f"Generated {final_event_count:,} activity events")
    print(f"Generated {len(attempts):,} assessment attempts")


if __name__ == "__main__":
    generate_activity_data()
