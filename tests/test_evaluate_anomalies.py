
import csv

import pytest

from src.validation import evaluate_anomalies as evaluator


FIELDS = ["record_id", "issue_type", "expected_decision"]


def write_ground_truth(path, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def make_finding(record, issue_type):
    return {
        "record": record,
        "issue_type": issue_type,
        "details": "Test finding",
    }


def setup_evaluation(tmp_path, monkeypatch, rows, findings):
    database_path = tmp_path / "fake.db"
    database_path.touch()

    ground_truth_path = tmp_path / "ground_truth.csv"
    write_ground_truth(ground_truth_path, rows)

    monkeypatch.setattr(
        evaluator, "GROUND_TRUTH_PATH", ground_truth_path
    )
    monkeypatch.setattr(
        evaluator, "detect_anomalies",
        lambda database_path: findings,
    )

    return database_path


def test_evaluation_separates_review_cases_from_actionable_anomalies(
    tmp_path, monkeypatch
):
    rows = [
        {
            "record_id": "EVT-001",
            "issue_type": "duplicate_event",
            "expected_decision": "duplicate",
        },
        {
            "record_id": "EVT-002",
            "issue_type": "unenrolled_activity",
            "expected_decision": "invalid",
        },
        {
            "record_id": "EVT-003",
            "issue_type": "timezone_boundary",
            "expected_decision": "review",
        },
    ]

    findings = [
        make_finding("EVT-001", "duplicate_event"),
        make_finding("EVT-002", "unenrolled_activity"),
        make_finding("EVT-003", "timezone_boundary"),
    ]

    database_path = setup_evaluation(
        tmp_path, monkeypatch, rows, findings
    )
    result = evaluator.evaluate(database_path)

    assert result["true_positives"] == 2
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["review_cases"] == 1
    assert result["missed_review_cases"] == 0


def test_evaluation_counts_false_positives_and_false_negatives(
    tmp_path, monkeypatch
):
    rows = [
        {
            "record_id": "EVT-001",
            "issue_type": "duplicate_event",
            "expected_decision": "duplicate",
        },
        {
            "record_id": "EVT-002",
            "issue_type": "unenrolled_activity",
            "expected_decision": "invalid",
        },
    ]

    findings = [
        make_finding("EVT-001", "duplicate_event"),
        make_finding("EVT-999", "unenrolled_activity"),
    ]

    database_path = setup_evaluation(
        tmp_path, monkeypatch, rows, findings
    )
    result = evaluator.evaluate(database_path)

    assert result["true_positives"] == 1
    assert result["false_positives"] == 1
    assert result["false_negatives"] == 1
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5


def test_evaluation_rejects_unsupported_decision(
    tmp_path, monkeypatch
):
    rows = [
        {
            "record_id": "EVT-001",
            "issue_type": "duplicate_event",
            "expected_decision": "ignore",
        }
    ]

    database_path = setup_evaluation(
        tmp_path, monkeypatch, rows, []
    )

    with pytest.raises(ValueError, match="Unsupported expected_decision"):
        evaluator.evaluate(database_path)


def test_evaluation_rejects_conflicting_labels(
    tmp_path, monkeypatch
):
    rows = [
        {
            "record_id": "EVT-001",
            "issue_type": "timezone_boundary",
            "expected_decision": "invalid",
        },
        {
            "record_id": "EVT-001",
            "issue_type": "timezone_boundary",
            "expected_decision": "review",
        },
    ]

    database_path = setup_evaluation(
        tmp_path, monkeypatch, rows, []
    )

    with pytest.raises(ValueError, match="both actionable and review"):
        evaluator.evaluate(database_path)


def test_evaluation_handles_empty_ground_truth(
    tmp_path, monkeypatch
):
    database_path = setup_evaluation(
        tmp_path, monkeypatch, [], []
    )

    result = evaluator.evaluate(database_path)

    assert result["true_positives"] == 0
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0
    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["review_cases"] == 0
    assert result["missed_review_cases"] == 0
