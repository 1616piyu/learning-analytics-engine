
import sqlite3
from pathlib import Path

import pytest

from src.build_pipeline import build_pipeline
from src.validation.inject_anomalies import inject_anomalies


@pytest.fixture
def integrity_databases(tmp_path, monkeypatch):
    """Build clean and anomalous databases in temporary storage."""
    clean_db = tmp_path / "clean.db"
    anomaly_db = tmp_path / "anomaly.db"
    ground_truth = tmp_path / "ground_truth.csv"

    build_pipeline(clean_db)
    build_pipeline(anomaly_db)

    import src.validation.inject_anomalies as injector

    monkeypatch.setattr(injector, "DATABASE_PATH", anomaly_db)
    monkeypatch.setattr(injector, "GROUND_TRUTH_PATH", ground_truth)
    inject_anomalies()

    return clean_db, anomaly_db


@pytest.fixture
def integrity_validator(monkeypatch):
    """Validate the database path selected by each test."""
    def _validate(db_path):
        import src.validation.integrity as integrity

        monkeypatch.setattr(
            integrity, "DATABASE_PATH", Path(db_path)
        )
        return integrity.validate_database()

    return _validate


def test_clean_database_passes_integrity_checks(
    integrity_databases, integrity_validator
):
    clean_db, _ = integrity_databases
    assert integrity_validator(clean_db) is True


def test_anomaly_database_fails_integrity_checks(
    integrity_databases, integrity_validator
):
    _, anomaly_db = integrity_databases
    assert integrity_validator(anomaly_db) is False


def test_clean_database_has_no_foreign_key_violations(
    integrity_databases,
):
    clean_db, _ = integrity_databases

    with sqlite3.connect(clean_db) as conn:
        violations = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

    assert violations == []


def test_clean_database_has_expected_core_tables(integrity_databases):
    clean_db, _ = integrity_databases

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

    with sqlite3.connect(clean_db) as conn:
        actual_tables = {
            row[0]
            for row in conn.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
            """).fetchall()
        }

    assert expected_tables.issubset(actual_tables)
