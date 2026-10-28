
import tempfile
from pathlib import Path

from src.build_pipeline import build_pipeline
from src.validation.checksum import database_checksum

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_reproducibility_databases_exist():
    first = PROJECT_ROOT / "data" / "reproducibility_test.db"
    second = PROJECT_ROOT / "data" / "reproducibility_test_2.db"

    assert first.exists(), f"Missing database: {first}"
    assert second.exists(), f"Missing database: {second}"


def test_reproducibility_checksums_match():
    first = PROJECT_ROOT / "data" / "reproducibility_test.db"
    second = PROJECT_ROOT / "data" / "reproducibility_test_2.db"

    assert database_checksum(first) == database_checksum(second)


def test_fresh_pipeline_builds_are_reproducible():
    with tempfile.TemporaryDirectory(prefix="learning_analytics_test_") as temp_dir:
        temp_path = Path(temp_dir)
        first = temp_path / "first.db"
        second = temp_path / "second.db"

        first_path = build_pipeline(first)
        first_checksum = database_checksum(first_path)

        second_path = build_pipeline(second)
        second_checksum = database_checksum(second_path)

        assert first_checksum == second_checksum, (
            "Fresh builds produced different checksums.\n"
            f"First:  {first_checksum}\n"
            f"Second: {second_checksum}"
        )
