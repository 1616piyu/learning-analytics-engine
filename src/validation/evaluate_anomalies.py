
import csv
import os
from pathlib import Path

from src.validation.anomaly_detector import detect_anomalies


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GROUND_TRUTH_PATH = Path(
    os.environ.get(
        "LEARNING_ANALYTICS_GROUND_TRUTH",
        str(PROJECT_ROOT / "data" / "ground_truth" / "ground_truth.csv"),
    )
)

ACTIONABLE_DECISIONS = {"duplicate", "invalid"}
VALID_DECISIONS = ACTIONABLE_DECISIONS | {"review"}


def evaluate(database_path=None):
    """
    Evaluate anomaly findings against labelled ground truth.

    'duplicate' and 'invalid' are actionable decisions.
    'review' cases are reported separately and excluded from
    actionable precision and recall.

    Args:
        database_path: Optional SQLite database path. If omitted,
            use LEARNING_ANALYTICS_DB or the default database path.
    """
    if database_path is None:
        database_path = os.environ.get(
            "LEARNING_ANALYTICS_DB",
            str(PROJECT_ROOT / "data" / "learning_analytics.db"),
        )

    database_path = Path(database_path).resolve()

    if not database_path.is_file():
        raise FileNotFoundError(
            f"Database not found: {database_path}"
        )

    if not GROUND_TRUTH_PATH.is_file():
        raise FileNotFoundError(
            f"Ground-truth file not found: {GROUND_TRUTH_PATH}"
        )

    required_columns = {
        "record_id",
        "issue_type",
        "expected_decision",
    }

    with GROUND_TRUTH_PATH.open(
        newline="", encoding="utf-8"
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or not required_columns.issubset(
            reader.fieldnames
        ):
            raise ValueError(
                "Ground truth must contain columns: "
                f"{sorted(required_columns)}"
            )

        truth_rows = list(reader)

    actionable_truth = set()
    review_truth = set()

    for row in truth_rows:
        record_id = row["record_id"].strip()
        issue_type = row["issue_type"].strip()
        decision = row["expected_decision"].strip().lower()

        if not record_id or not issue_type:
            raise ValueError(
                "Ground-truth record_id and issue_type cannot be empty"
            )

        if decision not in VALID_DECISIONS:
            raise ValueError(
                f"Unsupported expected_decision {decision!r} "
                f"for record {record_id!r}"
            )

        key = (record_id, issue_type)

        if decision in ACTIONABLE_DECISIONS:
            actionable_truth.add(key)
        else:
            review_truth.add(key)

    # A record cannot simultaneously be actionable and review-only.
    conflicting_labels = actionable_truth & review_truth
    if conflicting_labels:
        raise ValueError(
            "Records cannot have both actionable and review labels: "
            f"{sorted(conflicting_labels)}"
        )

    findings = detect_anomalies(database_path)

    predicted = {
        (str(item["record"]), str(item["issue_type"]))
        for item in findings
    }

    # Review-labelled records are excluded from actionable metrics.
    actionable_predicted = predicted - review_truth

    true_positives = actionable_truth & actionable_predicted
    false_positives = actionable_predicted - actionable_truth
    false_negatives = actionable_truth - actionable_predicted

    detected_review_cases = review_truth & predicted
    missed_review_cases = review_truth - predicted

    precision = (
        len(true_positives) / len(actionable_predicted)
        if actionable_predicted else 0.0
    )

    recall = (
        len(true_positives) / len(actionable_truth)
        if actionable_truth else 0.0
    )

    print("\nANOMALY EVALUATION REPORT")
    print("=" * 40)
    print(f"Database: {database_path}")
    print(f"Ground truth: {GROUND_TRUTH_PATH}")
    print(f"Expected actionable labels: {len(actionable_truth)}")
    print(f"Detected actionable labels: {len(actionable_predicted)}")
    print(f"True positives: {len(true_positives)}")
    print(f"False positives: {len(false_positives)}")
    print(f"False negatives: {len(false_negatives)}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"Expected review cases: {len(review_truth)}")
    print(f"Detected review cases: {len(detected_review_cases)}")
    print(f"Missed review cases: {len(missed_review_cases)}")

    if false_positives:
        print("\nFalse positives:")
        for item in sorted(false_positives):
            print(item)

    if false_negatives:
        print("\nFalse negatives:")
        for item in sorted(false_negatives):
            print(item)

    if missed_review_cases:
        print("\nMissed review cases:")
        for item in sorted(missed_review_cases):
            print(item)

    return {
        "true_positives": len(true_positives),
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "precision": precision,
        "recall": recall,
        "review_cases": len(detected_review_cases),
        "missed_review_cases": len(missed_review_cases),
    }


if __name__ == "__main__":
    evaluate()
