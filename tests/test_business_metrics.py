
import sqlite3

import pytest

from src.build_pipeline import build_pipeline
from src.reporting.business_metrics import (
    get_cohort_performance,
    get_inactive_enrollment_metrics,
)
from src.reporting.generate_report import build_report


@pytest.fixture
def report_database(tmp_path, monkeypatch):
    """Build an isolated database for analytics tests."""
    database_path = tmp_path / "business_metrics_test.db"

    monkeypatch.setenv(
        "LEARNING_ANALYTICS_DB",
        str(database_path),
    )

    build_pipeline(database_path)
    return database_path


def test_report_includes_cohort_performance(report_database):
    report = build_report(report_database)
    cohorts = report["cohort_performance"]

    assert len(cohorts) == 4
    assert sum(c["learners"] for c in cohorts) == 100
    assert sum(c["enrollments"] for c in cohorts) == 386

    for cohort in cohorts:
        assert cohort["completed_enrollments"] <= cohort["enrollments"]

        rate = cohort["completion_rate_pct"]
        if cohort["enrollments"] > 0:
            assert rate is not None
            assert 0 <= rate <= 100


def test_report_includes_inactivity_metrics(report_database):
    report = build_report(report_database)
    metrics = report["inactive_enrollments"]

    assert metrics["inactivity_days"] == 30
    assert metrics["reference_time_utc"].startswith(
        "2026-10-22T12:00:00"
    )
    assert metrics["ongoing_enrollments"] >= 0
    assert (
        0
        <= metrics["inactive_enrollments"]
        <= metrics["ongoing_enrollments"]
    )
    assert len(metrics["courses"]) == 10

    assert sum(
        course["ongoing_enrollments"]
        for course in metrics["courses"]
    ) == metrics["ongoing_enrollments"]

    assert sum(
        course["inactive_enrollments"]
        for course in metrics["courses"]
    ) == metrics["inactive_enrollments"]


def test_inactivity_window_must_be_positive(report_database):
    with sqlite3.connect(report_database) as conn:
        with pytest.raises(ValueError):
            get_inactive_enrollment_metrics(conn, inactivity_days=0)


def test_cohort_metrics_include_all_cohorts(report_database):
    with sqlite3.connect(report_database) as conn:
        cohorts = get_cohort_performance(conn)

    assert len(cohorts) == 4
    assert len({cohort["cohort_id"] for cohort in cohorts}) == 4
