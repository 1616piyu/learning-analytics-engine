
import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "data" / "learning_analytics_full.db"
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
BATCH_SIZE = 10_000

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


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def record_export(manifest, path):
    manifest["exports"][path.name] = {
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def export_dataset(database_path=DEFAULT_DB, export_dir=EXPORT_DIR):
    database_path = Path(database_path).resolve()
    export_dir = Path(export_dir).resolve()

    if not database_path.exists():
        raise FileNotFoundError(f"Database not found: {database_path}")

    export_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "database": database_path.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "exports": {},
        "tables": {},
    }

    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row

    try:
        foreign_key_errors = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if foreign_key_errors:
            raise RuntimeError(
                f"Database has {len(foreign_key_errors)} "
                "foreign-key violations"
            )

        for table in TABLES:
            columns = [
                row["name"]
                for row in conn.execute(f"PRAGMA table_info({table})")
            ]

            if not columns:
                raise RuntimeError(f"Missing expected table: {table}")

            # Use the first column as the stable export ordering.
            cursor = conn.execute(
                f'SELECT * FROM "{table}" ORDER BY 1'
            )

            csv_path = export_dir / f"{table.lower()}.csv"
            jsonl_path = export_dir / f"{table.lower()}.jsonl"
            row_count = 0

            with (
                csv_path.open(
                    "w", newline="", encoding="utf-8-sig"
                ) as csv_file,
                jsonl_path.open(
                    "w", encoding="utf-8"
                ) as jsonl_file,
            ):
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(columns)

                while True:
                    batch = cursor.fetchmany(BATCH_SIZE)

                    if not batch:
                        break

                    csv_writer.writerows(
                        [row[column] for column in columns]
                        for row in batch
                    )

                    for row in batch:
                        jsonl_file.write(
                            json.dumps(
                                dict(row),
                                ensure_ascii=False,
                                default=str,
                            )
                            + "\n"
                        )

                    row_count += len(batch)

            manifest["tables"][table] = {
                "rows": row_count,
                "columns": columns,
                "csv_file": csv_path.name,
                "jsonl_file": jsonl_path.name,
            }

            record_export(manifest, csv_path)
            record_export(manifest, jsonl_path)

            print(
                f"Exported {table}: {row_count:,} rows "
                f"(CSV + JSONL)"
            )

        # SQL seed contains the database schema and table data.
        sql_path = export_dir / "learning_analytics_seed.sql"

        with sql_path.open("w", encoding="utf-8") as sql_file:
            for line in conn.iterdump():
                sql_file.write(line + "\n")

        record_export(manifest, sql_path)

        # Summary contains counts; JSONL files contain the actual records.
        summary = {
            "database": database_path.name,
            "generated_at_utc": manifest["generated_at_utc"],
            "tables": {
                table: details["rows"]
                for table, details in manifest["tables"].items()
            },
            "total_tables": len(manifest["tables"]),
            "foreign_key_violations": 0,
            "formats": ["CSV", "JSONL", "SQL"],
        }

        json_path = export_dir / "dataset_summary.json"
        json_path.write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )
        record_export(manifest, json_path)

        # Write the manifest last so it includes every data export.
        manifest_path = export_dir / "export_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

        print("\nDATASET EXPORT COMPLETED")
        print("=" * 40)
        print(f"Source database: {database_path}")
        print(f"Export directory: {export_dir}")
        print(f"Tables exported: {len(TABLES)}")
        print("Formats: CSV, JSONL, SQL")
        print(f"SQL seed: {sql_path.name}")
        print(f"JSON summary: {json_path.name}")
        print(f"Manifest: {manifest_path.name}")

    finally:
        conn.close()


if __name__ == "__main__":
    export_dataset()
