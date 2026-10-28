
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEAN_DB = PROJECT_ROOT / "data" / "reproducibility_test.db"
ANOMALY_DB = PROJECT_ROOT / "data" / "anomaly_test.db"

EXPECTED_ANOMALIES = {
    ("EVT-ANOMALY-DUP-000001", "duplicate_event"),
    ("EVT-ANOMALY-DUP-000002", "duplicate_event"),
    ("EVT-ANOMALY-UNENROLLED-000001", "unenrolled_activity"),
    ("OUT-ANOMALY-000001", "completion_before_assessment"),
    ("EVT-ANOMALY-TZ-000001", "timezone_boundary"),
}


@pytest.fixture
def detector_for_db(monkeypatch):
    """Load the detector with an explicitly selected database."""

    def _load(db_path):
        if not db_path.exists():
            pytest.fail(f"Required test database not found: {db_path}")

        monkeypatch.setenv("LEARNING_ANALYTICS_DB", str(db_path))

        # The detector captures DB_PATH during module import.
        import src.validation.anomaly_detector as detector

        # Ensure tests use the selected database even if the module
        # was imported earlier by another test.
        detector.DB_PATH = Path(os.environ["LEARNING_ANALYTICS_DB"])

        return detector.detect_anomalies

    return _load


def test_detector_returns_a_list(detector_for_db):
    detect_anomalies = detector_for_db(ANOMALY_DB)

    findings = detect_anomalies()

    assert isinstance(findings, list)


def test_clean_database_has_no_anomalies(detector_for_db):
    detect_anomalies = detector_for_db(CLEAN_DB)

    findings = detect_anomalies()

    assert findings == []


def test_all_injected_anomalies_are_detected(detector_for_db):
    detect_anomalies = detector_for_db(ANOMALY_DB)

    findings = detect_anomalies()

    detected = {
        (item["record"], item["issue_type"])
        for item in findings
    }

    assert EXPECTED_ANOMALIES.issubset(detected)


def test_injected_anomalies_have_no_unexpected_findings(detector_for_db):
    detect_anomalies = detector_for_db(ANOMALY_DB)

    findings = detect_anomalies()

    detected = {
        (item["record"], item["issue_type"])
        for item in findings
    }

    assert detected == EXPECTED_ANOMALIES


def test_findings_have_required_fields(detector_for_db):
    detect_anomalies = detector_for_db(ANOMALY_DB)

    findings = detect_anomalies()

    for finding in findings:
        assert finding["record"]
        assert finding["issue_type"]
        assert finding["details"]
