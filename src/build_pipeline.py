
import argparse
import importlib
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from src.generator.config import SCALE_PROFILES

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "anomaly_test.db"


def build_pipeline(database_path=None, scale="starter"):
    if scale not in SCALE_PROFILES:
        raise ValueError(f"Unknown scale {scale!r}; use 'starter' or 'full'")

    profile = SCALE_PROFILES[scale]

    if database_path is not None:
        build_db_path = Path(database_path)
    elif os.environ.get("LEARNING_ANALYTICS_DB"):
        build_db_path = Path(os.environ["LEARNING_ANALYTICS_DB"])
    else:
        filename = (
            "learning_analytics_full.db"
            if scale == "full"
            else "anomaly_test.db"
        )
        build_db_path = PROJECT_ROOT / "data" / filename

    build_db_path = build_db_path.resolve()
    build_db_path.parent.mkdir(parents=True, exist_ok=True)

    if build_db_path.exists():
        raise FileExistsError(
            f"{build_db_path} already exists. Choose a new path; "
            "existing databases are never overwritten."
        )

    os.environ["LEARNING_ANALYTICS_DB"] = str(build_db_path)

    module_names = [
        "src.generator.config",
        "src.database.init_db",
        "src.generator.master_data",
        "src.generator.course_structure",
        "src.generator.enrollments",
        "src.generator.activity_data",
        "src.generator.course_outcomes",
    ]

    modules = {}
    for name in module_names:
        module = importlib.import_module(name)
        modules[name] = importlib.reload(module)

    modules["src.database.init_db"].initialize_database()

    modules["src.generator.master_data"].generate_master_data(
        learner_count=profile["learners"],
        course_count=profile["courses"],
        cohort_count=profile["cohorts"],
    )
    modules["src.generator.course_structure"].generate_course_structure()

    modules["src.generator.enrollments"].generate_enrollments(
        target_enrollment_count=profile["enrollments"],
    )

    modules["src.generator.activity_data"].generate_activity_data(
        target_event_count=profile["activity_events"],
    )

    modules["src.generator.course_outcomes"].generate_course_outcomes()

    with closing(sqlite3.connect(build_db_path)) as conn:
        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise RuntimeError(f"Foreign-key violations: {fk_errors[:10]}")

        counts = {}
        for table in (
            "Learner", "Course", "Enrollment", "ActivityEvent",
            "Attempt", "CourseOutcome",
        ):
            counts[table] = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

    if scale == "full":
        expected = {
            "Learner": 20_000,
            "Course": 500,
            "Enrollment": 100_000,
            "ActivityEvent": 2_000_000,
        }
        mismatches = {
            table: (counts[table], count)
            for table, count in expected.items()
            if counts[table] != count
        }
        if mismatches:
            raise RuntimeError(
                f"Full-scale count validation failed (actual, expected): "
                f"{mismatches}"
            )

    print("\nPipeline completed.")
    print(f"Scale: {scale}")
    print(f"Database: {build_db_path}")
    print("Foreign-key validation: PASSED")
    for table, count in counts.items():
        print(f"{table}: {count:,}")

    return build_db_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=["starter", "full"], default="starter")
    parser.add_argument("--db", help="New database path; must not already exist")
    args = parser.parse_args()
    build_pipeline(database_path=args.db, scale=args.scale)
