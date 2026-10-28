
import os
import random
import sqlite3
from contextlib import closing
from pathlib import Path

from src.generator.config import REFERENCE_TIME, SEED


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = Path(
    os.environ.get(
        "LEARNING_ANALYTICS_DB",
        str(PROJECT_ROOT / "data" / "learning_analytics.db"),
    )
)


def generate_course_structure():
    rng = random.Random(SEED)

    content_rows = []
    assessment_rows = []
    rule_rows = []

    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")

            courses = conn.execute(
                """
                SELECT course_id
                FROM Course
                ORDER BY course_id
                """
            ).fetchall()

            effective_from = REFERENCE_TIME.replace(
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ).isoformat()

            for course_number, (course_id,) in enumerate(
                courses, start=1
            ):
                module_id = f"CNT-{course_number:06d}-001"

                # Parent module
                content_rows.append((
                    module_id,
                    course_id,
                    None,
                    "Module 1: Introduction",
                    "module",
                    1,
                    0,
                ))

                # Three required lessons under the module
                for lesson_number in range(1, 4):
                    content_id = (
                        f"CNT-{course_number:06d}-"
                        f"{lesson_number + 1:03d}"
                    )

                    content_rows.append((
                        content_id,
                        course_id,
                        module_id,
                        f"Lesson {lesson_number}",
                        rng.choice(["video", "reading"]),
                        lesson_number + 1,
                        1,
                    ))

                # One required assessment per course
                assessment_rows.append((
                    f"ASM-2026-{course_number:06d}",
                    course_id,
                    "Final Assessment",
                    60.0,
                    1,
                ))

                # Require three lessons and a passing assessment
                rule_rows.append((
                    f"RULE-{course_number:06d}-001",
                    course_id,
                    effective_from,
                    None,
                    3,
                    1,
                    1,
                ))

            conn.executemany(
                """
                INSERT INTO ContentItem (
                    content_id, course_id, parent_content_id,
                    title, content_type, sequence_number, is_required
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                content_rows,
            )

            conn.executemany(
                """
                INSERT INTO Assessment (
                    assessment_id, course_id, title,
                    passing_score, is_required
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                assessment_rows,
            )

            conn.executemany(
                """
                INSERT INTO CompletionRule (
                    rule_id, course_id, effective_from, effective_to,
                    required_content_count, require_assessment_pass,
                    rule_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rule_rows,
            )

    print(f"Generated {len(content_rows)} content items")
    print(f"Generated {len(assessment_rows)} assessments")
    print(f"Generated {len(rule_rows)} completion rules")


if __name__ == "__main__":
    generate_course_structure()
