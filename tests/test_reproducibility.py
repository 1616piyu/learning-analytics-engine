
import tempfile
from pathlib import Path

from src.build_pipeline import build_pipeline
from src.validation.checksum import database_checksum


def test_fresh_pipeline_builds_are_reproducible():
    with tempfile.TemporaryDirectory(
        prefix="learning_analytics_test_"
    ) as temp_dir:
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
