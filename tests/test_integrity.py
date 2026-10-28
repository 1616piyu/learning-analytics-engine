
import os
import sqlite3
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEAN_DB = PROJECT_ROOT / "data" / "reproducibility_test.db"
ANOMALY_DB = PROJECT_ROOT / "data" / "anomaly_test.db"


@pytest.fixture
def integrity_validator(monkeypatch):
    """Load the integrity validator against a selected database."""

    def _validate(db_path):
        if not db_path.exists():
            pytest.fail(f"Required test database not found: {db_path}")

        monkeypatch.setenv("LEARNING_ANALYTICS_DB", str(db_path))

        import src.validation.integrity as integrity

        # The module reads its database path at import time.
        integrity.DATABASE_PATH = Path(
            os.environ["LEARNING_ANALYTICS_DB"]
        )

        return integrity.validate_database()

    return _validate


def test_clean_database_passes_integrity_checks(integrity_validator):
    assert integrity_validator(CLEAN_DB) is True


def test_anomaly_database_fails_integrity_checks(integrity_validator):
    # The injected unenrolled activity is intentionally invalid.
    assert integrity_validator(ANOMALY_DB) is False


def test_clean_database_has_no_foreign_key_violations():
    assert CLEAN_DB.exists(), f"Missing database: {CLEAN_DB}"

    with sqlite3.connect(CLEAN_DB) as conn:
        violations = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

    assert violations == []


def test_clean_database_has_expected_core_tables():
    assert CLEAN_DB.exists(), f"Missing database: {CLEAN_DB}"

    expected_tables = {
        "Learner",
        "Course",
        "Cohort",
        "LearnerCohort",
        "Enrollment",
        "ContentItem",
        "Assessment",
        "CompletionRule",
        "ActivityEvent",
        "Attempt",
        "CourseOutcome",
    }

    with sqlite3.connect(CLEAN_DB) as conn:
        actual_tables = {
            row[0]
            for row in conn.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
            """).fetchall()
        }

    assert expected_tables.issubset(actual_tables)
