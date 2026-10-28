
import importlib
import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "anomaly_test.db"


def build_pipeline(database_path=None):
    """
    Build the learning analytics database from scratch.

    The database path is selected in this order:
    1. Explicit database_path argument.
    2. LEARNING_ANALYTICS_DB environment variable.
    3. DEFAULT_DB_PATH.

    Existing databases are never overwritten.
    """

    # Resolve the target database path before loading any generators.
    if database_path is not None:
        build_db_path = Path(database_path)
    elif os.environ.get("LEARNING_ANALYTICS_DB"):
        build_db_path = Path(os.environ["LEARNING_ANALYTICS_DB"])
    else:
        build_db_path = DEFAULT_DB_PATH

    build_db_path = build_db_path.resolve()
    build_db_path.parent.mkdir(parents=True, exist_ok=True)

    # Protect existing databases from accidental overwrites.
    if build_db_path.exists():
        raise FileExistsError(
            f"{build_db_path} already exists. "
            "Choose a new database path before rebuilding."
        )

    # Make the selected path available to database and generator modules.
    os.environ["LEARNING_ANALYTICS_DB"] = str(build_db_path)

    # Reload configuration first so cached database paths are refreshed.
    config_name = "src.generator.config"
    config_module = importlib.import_module(config_name)
    importlib.reload(config_module)

    # Reload each module after configuration has been refreshed.
    module_names = [
        "src.database.init_db",
        "src.generator.master_data",
        "src.generator.course_structure",
        "src.generator.enrollments",
        "src.generator.activity_data",
        "src.generator.course_outcomes",
    ]

    modules = {}

    for module_name in module_names:
        module = importlib.import_module(module_name)
        modules[module_name] = importlib.reload(module)

    # Step 1: Initialize the database schema.
    modules["src.database.init_db"].initialize_database()

    # Step 2: Generate learners, courses, and cohorts.
    modules["src.generator.master_data"].generate_master_data()

    # Step 3: Generate course content, assessments, and completion rules.
    modules["src.generator.course_structure"].generate_course_structure()

    # Step 4: Generate learner enrollments.
    modules["src.generator.enrollments"].generate_enrollments()

    # Step 5: Generate learner activity events.
    modules["src.generator.activity_data"].generate_activity_data()

    # Step 6: Calculate course outcomes.
    modules["src.generator.course_outcomes"].generate_course_outcomes()

    # Step 7: Validate foreign-key relationships and close the connection.
    with closing(sqlite3.connect(build_db_path)) as conn:
        foreign_key_errors = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

    if foreign_key_errors:
        raise RuntimeError(
            "Foreign-key violations found: "
            f"{foreign_key_errors}"
        )

    print("\nPipeline completed successfully.")
    print(f"Database: {build_db_path}")
    print("Foreign-key validation: PASSED")

    return build_db_path


if __name__ == "__main__":
    build_pipeline()
