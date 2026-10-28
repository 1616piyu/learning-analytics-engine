
import os
from pathlib import Path

from src.validation.inject_anomalies import inject_anomalies
import sqlite3

import pytest

from src.build_pipeline import build_pipeline
from src.reporting.generate_report import build_report, write_report


@pytest.fixture
def report_database(tmp_path, monkeypatch):
    """Build an isolated database for reporting tests."""
    database_path = tmp_path / "report_test.db"

    # Restore the original environment variable after each test.
    monkeypatch.setenv(
        "LEARNING_ANALYTICS_DB",
        str(database_path),
    )

    build_pipeline(database_path)

    return database_path


def test_report_contains_expected_overview(report_database):
    report = build_report(report_database)
    overview = report["overview"]

    assert overview["learners"] == 100
    assert overview["courses"] == 10
    assert overview["enrollments"] == 386
    assert overview["activity_events"] == 695
    assert overview["assessment_attempts"] == 482
    assert overview["course_outcomes"] == 386


def test_report_completion_metrics_are_valid(report_database):
    report = build_report(report_database)

    assert len(report["course_completion"]) == 10

    for course in report["course_completion"]:
        assert course["total_enrollments"] >= 0
        assert course["completed_enrollments"] <= (
            course["total_enrollments"]
        )

        rate = course["completion_rate_pct"]
        if course["total_enrollments"] > 0:
            assert rate is not None
            assert 0 <= rate <= 100


def test_report_assessment_and_engagement_metrics(report_database):
    report = build_report(report_database)

    assert len(report["assessment_performance"]) == 10
    assert len(report["learner_engagement"]) == 10

    total_attempts = sum(
        course["total_attempts"]
        for course in report["assessment_performance"]
    )
    total_events = sum(
        course["total_events"]
        for course in report["learner_engagement"]
    )

    assert total_attempts == 482
    assert total_events == 695


def test_report_data_quality_checks_pass(report_database):
    report = build_report(report_database)
    quality = report["data_quality"]

    assert quality["checks_run"] > 0
    assert quality["failed_checks"] == 0
    assert quality["foreign_key_violation_count"] == 0


def test_report_does_not_modify_database(report_database):
    with sqlite3.connect(report_database) as conn:
        before = {
            table: conn.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
            for table in [
                "Learner",
                "Course",
                "Enrollment",
                "ActivityEvent",
                "Attempt",
                "CourseOutcome",
            ]
        }

    build_report(report_database)

    with sqlite3.connect(report_database) as conn:
        after = {
            table: conn.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
            for table in before
        }

    assert after == before


def test_report_writer_refuses_to_overwrite(tmp_path):
    output_path = tmp_path / "report.json"
    output_path.write_text("existing report", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_report({}, output_path)

    assert output_path.read_text(encoding="utf-8") == "existing report"


def test_report_includes_anomaly_summary(report_database):
    report = build_report(report_database)
    anomaly_report = report["anomaly_detection"]

    findings = anomaly_report["findings"]

    assert anomaly_report["total_findings"] == len(findings)

    expected_status = (
        "clean" if not findings else "needs_investigation"
    )
    assert anomaly_report["status"] == expected_status

    expected_counts = {}
    for finding in findings:
        issue_type = finding["issue_type"]
        expected_counts[issue_type] = (
            expected_counts.get(issue_type, 0) + 1
        )

    assert anomaly_report["findings_by_type"] == dict(
        sorted(expected_counts.items())
    )


def test_report_anomaly_summary_matches_findings(report_database):
    report = build_report(report_database)

    anomaly_report = report["anomaly_detection"]
    findings = anomaly_report["findings"]

    assert anomaly_report["total_findings"] == len(findings)

    counts = {}
    for finding in findings:
        issue_type = finding["issue_type"]
        counts[issue_type] = counts.get(issue_type, 0) + 1

    assert anomaly_report["findings_by_type"] == dict(
        sorted(counts.items())
    )

    expected_status = (
        "clean" if not findings else "needs_investigation"
    )
    assert anomaly_report["status"] == expected_status


def test_anomaly_reporting_does_not_modify_database(report_database):
    with sqlite3.connect(report_database) as conn:
        before = {
            table: conn.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
            for table in [
                "Learner",
                "Course",
                "Enrollment",
                "ActivityEvent",
                "Attempt",
                "CourseOutcome",
            ]
        }

    build_report(report_database)

    with sqlite3.connect(report_database) as conn:
        after = {
            table: conn.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
            for table in before
        }

    assert after == before


def test_report_detects_injected_anomalies(tmp_path, monkeypatch):
    from src.build_pipeline import build_pipeline

    database_path = tmp_path / "anomaly_reporting_test.db"
    ground_truth_path = tmp_path / "anomaly_reporting_ground_truth.csv"

    monkeypatch.setenv(
        "LEARNING_ANALYTICS_DB",
        str(database_path),
    )
    monkeypatch.setenv(
        "LEARNING_ANALYTICS_GROUND_TRUTH",
        str(ground_truth_path),
    )

    # Build an isolated database for this test.
    build_pipeline(database_path)

    # Inject the known test anomalies into this database.
    import src.validation.inject_anomalies as injector
    injector.DATABASE_PATH = Path(database_path)
    injector.GROUND_TRUTH_PATH = Path(ground_truth_path)
    inject_anomalies()

    # Generate the report from the same database.
    report = build_report(database_path)
    anomaly_report = report["anomaly_detection"]

    assert anomaly_report["total_findings"] > 0
    assert anomaly_report["status"] == "needs_investigation"

    detected_types = {
        finding["issue_type"]
        for finding in anomaly_report["findings"]
    }

    assert "duplicate_event" in detected_types
    assert "unenrolled_activity" in detected_types
    assert "completion_before_assessment" in detected_types
    assert "timezone_boundary" in detected_types

    assert ground_truth_path.exists()
