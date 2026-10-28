
from pathlib import Path

import pytest

from src.build_pipeline import build_pipeline
from src.validation.inject_anomalies import inject_anomalies


EXPECTED_ANOMALIES = {
    ("EVT-ANOMALY-DUP-000001", "duplicate_event"),
    ("EVT-ANOMALY-DUP-000002", "duplicate_event"),
    ("EVT-ANOMALY-UNENROLLED-000001", "unenrolled_activity"),
    ("OUT-ANOMALY-000001", "completion_before_assessment"),
    ("EVT-ANOMALY-TZ-000001", "timezone_boundary"),
}


@pytest.fixture
def detector_databases(tmp_path, monkeypatch):
    """Create clean and anomaly-injected databases in temporary storage."""
    clean_db = tmp_path / "clean.db"
    anomaly_db = tmp_path / "anomaly.db"
    ground_truth = tmp_path / "ground_truth.csv"

    build_pipeline(clean_db)
    build_pipeline(anomaly_db)

    import src.validation.inject_anomalies as injector

    monkeypatch.setattr(injector, "DATABASE_PATH", anomaly_db)
    monkeypatch.setattr(injector, "GROUND_TRUTH_PATH", ground_truth)
    inject_anomalies()

    import src.validation.anomaly_detector as detector

    return clean_db, anomaly_db, detector.detect_anomalies


def test_detector_returns_a_list(detector_databases):
    _, anomaly_db, detect_anomalies = detector_databases

    findings = detect_anomalies(anomaly_db)

    assert isinstance(findings, list)


def test_clean_database_has_no_anomalies(detector_databases):
    clean_db, _, detect_anomalies = detector_databases

    assert detect_anomalies(clean_db) == []


def test_all_injected_anomalies_are_detected(detector_databases):
    _, anomaly_db, detect_anomalies = detector_databases

    findings = detect_anomalies(anomaly_db)
    detected = {
        (item["record"], item["issue_type"])
        for item in findings
    }

    assert EXPECTED_ANOMALIES.issubset(detected)


def test_injected_anomalies_have_no_unexpected_findings(
    detector_databases,
):
    _, anomaly_db, detect_anomalies = detector_databases

    findings = detect_anomalies(anomaly_db)
    detected = {
        (item["record"], item["issue_type"])
        for item in findings
    }

    assert detected == EXPECTED_ANOMALIES


def test_findings_have_required_fields(detector_databases):
    _, anomaly_db, detect_anomalies = detector_databases

    findings = detect_anomalies(anomaly_db)

    for finding in findings:
        assert finding["record"]
        assert finding["issue_type"]
        assert finding["details"]
