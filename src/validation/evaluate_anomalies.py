
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


def evaluate():
    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(
            f"Ground-truth file not found: {GROUND_TRUTH_PATH}"
        )

    with GROUND_TRUTH_PATH.open(
        newline="", encoding="utf-8"
    ) as file:
        reader = csv.DictReader(file)
        required_columns = {"record_id", "issue_type", "expected_decision"}

        if not reader.fieldnames or not required_columns.issubset(
            reader.fieldnames
        ):
            raise ValueError(
                f"Ground truth must contain columns: {sorted(required_columns)}"
            )

        truth_rows = list(reader)

    truth = {
        (row["record_id"], row["issue_type"])
        for row in truth_rows
    }

    findings = detect_anomalies()

    predicted = {
        (item["record"], item["issue_type"])
        for item in findings
    }

    true_positives = truth & predicted
    false_positives = predicted - truth
    false_negatives = truth - predicted

    precision = (
        len(true_positives) / len(predicted)
        if predicted else 0.0
    )

    recall = (
        len(true_positives) / len(truth)
        if truth else 0.0
    )

    print("\nANOMALY EVALUATION REPORT")
    print("=" * 40)
    print(f"Database: configured by LEARNING_ANALYTICS_DB")
    print(f"Ground truth: {GROUND_TRUTH_PATH}")
    print(f"Expected labels: {len(truth)}")
    print(f"Detected labels: {len(predicted)}")
    print(f"True positives: {len(true_positives)}")
    print(f"False positives: {len(false_positives)}")
    print(f"False negatives: {len(false_negatives)}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")

    if false_positives:
        print("\nFalse positives:")
        for item in sorted(false_positives):
            print(item)

    if false_negatives:
        print("\nFalse negatives:")
        for item in sorted(false_negatives):
            print(item)

    return {
        "true_positives": len(true_positives),
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "precision": precision,
        "recall": recall,
    }


if __name__ == "__main__":
    evaluate()
