

import os
import sqlite3
from contextlib import closing
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = Path(
    os.environ.get(
        "LEARNING_ANALYTICS_DB",
        str(PROJECT_ROOT / "data" / "learning_analytics.db"),
    )
)

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def initialize_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        with connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(schema)

            result = connection.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()

            if result:
                raise RuntimeError(
                    f"Foreign key violations: {result}"
                )

    print(f"Database initialized: {DATABASE_PATH}")


if __name__ == "__main__":
    initialize_database()
