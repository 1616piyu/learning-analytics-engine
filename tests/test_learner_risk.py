
import sqlite3

import pytest

from src.build_pipeline import build_pipeline
from src.reporting.learner_risk import get_learner_risk_metrics


@pytest.fixture
def risk_database(tmp_path):
    database_path = tmp_path / "learner_risk_test.db"
    build_pipeline(database_path)
    return database_path


def test_risk_report_contains_all_ongoing_enrollments(risk_database):
    with sqlite3.connect(risk_database) as conn:
        metrics = get_learner_risk_metrics(conn)

    assert metrics["total_ongoing_enrollments"] == sum(
        1 for item in metrics["enrollments"]
    )

    assert (
        metrics["high_risk_enrollments"]
        + metrics["medium_risk_enrollments"]
        + metrics["low_risk_enrollments"]
        == metrics["total_ongoing_enrollments"]
    )


def test_risk_scores_and_levels_are_valid(risk_database):
    with sqlite3.connect(risk_database) as conn:
        metrics = get_learner_risk_metrics(conn)

    for item in metrics["enrollments"]:
        assert 0 <= item["risk_score"] <= 100
        assert item["risk_level"] in {"low", "medium", "high"}
        assert item["recommended_intervention"]
        assert isinstance(item["risk_reasons"], list)


def test_inactivity_window_must_be_positive(risk_database):
    with sqlite3.connect(risk_database) as conn:
        with pytest.raises(ValueError):
            get_learner_risk_metrics(conn, inactivity_days=0)


def test_boolean_is_not_a_valid_inactivity_window(risk_database):
    with sqlite3.connect(risk_database) as conn:
        with pytest.raises(ValueError):
            get_learner_risk_metrics(conn, inactivity_days=True)
