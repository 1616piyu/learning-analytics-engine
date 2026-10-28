
import csv

from src.validation import evaluate_anomalies as evaluator


def test_evaluation_separates_review_cases_from_actionable_anomalies(
    tmp_path, monkeypatch
):
    ground_truth_path = tmp_path / "ground_truth.csv"
    database_path = tmp_path / "fake.db"

    # The evaluator checks that the database file exists.
    # The detector is mocked, so an empty placeholder is sufficient.
    database_path.touch()

    with ground_truth_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "record_id",
                "issue_type",
                "expected_decision",
            ],
        )
        writer.writeheader()
        writer.writerows([
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
        ])

    monkeypatch.setattr(
        evaluator, "GROUND_TRUTH_PATH", ground_truth_path
    )
    monkeypatch.setattr(
        evaluator,
        "detect_anomalies",
        lambda database_path: [
            {
                "record": "EVT-001",
                "issue_type": "duplicate_event",
                "details": "Duplicate source event",
            },
            {
                "record": "EVT-002",
                "issue_type": "unenrolled_activity",
                "details": "Missing enrollment",
            },
            {
                "record": "EVT-003",
                "issue_type": "timezone_boundary",
                "details": "Local date differs from UTC date",
            },
        ],
    )

    result = evaluator.evaluate(database_path)

    assert result["true_positives"] == 2
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["review_cases"] == 1
