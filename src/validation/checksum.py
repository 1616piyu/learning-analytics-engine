
import hashlib
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

TABLES = [
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
]


def database_checksum(database_path):
    database_path = Path(database_path)

    with closing(sqlite3.connect(database_path)) as conn:
        table_hashes = {}

        for table in TABLES:
            rows = conn.execute(
                f'SELECT * FROM "{table}" ORDER BY 1'
            ).fetchall()

            canonical_rows = json.dumps(
                rows,
                separators=(",", ":"),
                ensure_ascii=False,
            )

            table_hashes[table] = hashlib.sha256(
                canonical_rows.encode("utf-8")
            ).hexdigest()

    combined = json.dumps(table_hashes, sort_keys=True)

    return hashlib.sha256(
        combined.encode("utf-8")
    ).hexdigest()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m src.validation.checksum <database_path>"
        )

    print(database_checksum(sys.argv[1]))
