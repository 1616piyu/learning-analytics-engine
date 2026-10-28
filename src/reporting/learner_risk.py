
"""Explainable learner risk analytics."""

from datetime import timedelta

from src.generator.config import REFERENCE_TIME


def get_learner_risk_metrics(conn, inactivity_days=30):
    """
    Calculate explainable risk metrics for ongoing enrollments.

    Risk signals:
    - No activity within the configured inactivity window.
    - Low latest graded assessment score.
    - Repeated failed graded attempts.
    - Low recorded course completion.

    Risk scores are rule-based indicators, not predictions of dropout.
    """
    if (
        not isinstance(inactivity_days, int)
        or isinstance(inactivity_days, bool)
        or inactivity_days < 1
    ):
        raise ValueError("inactivity_days must be a positive integer")

    as_of = REFERENCE_TIME
    cutoff = as_of - timedelta(days=inactivity_days)

    rows = conn.execute(
        """
        WITH recent_activity AS (
            SELECT
                enrollment_id,
                MAX(datetime(event_time)) AS last_activity
            FROM ActivityEvent
            WHERE enrollment_id IS NOT NULL
              AND datetime(event_time) <= datetime(?)
            GROUP BY enrollment_id
        ),
        graded_attempts AS (
            SELECT
                a.enrollment_id,
                a.assessment_id,
                a.attempt_number,
                a.score,
                a.submitted_at,
                s.passing_score,
                ROW_NUMBER() OVER (
                    PARTITION BY a.enrollment_id, a.assessment_id
                    ORDER BY
                        a.attempt_number DESC,
                        a.started_at DESC
                ) AS attempt_rank
            FROM Attempt a
            JOIN Assessment s
                ON s.assessment_id = a.assessment_id
            WHERE a.status = 'graded'
              AND a.score IS NOT NULL
              AND datetime(a.started_at) <= datetime(?)
        ),
        assessment_metrics AS (
            SELECT
                enrollment_id,
                AVG(
                    CASE WHEN attempt_rank = 1 THEN score END
                ) AS avg_latest_score,
                SUM(
                    CASE
                        WHEN score < passing_score THEN 1
                        ELSE 0
                    END
                ) AS failed_attempts
            FROM graded_attempts
            GROUP BY enrollment_id
        )
        SELECT
            e.enrollment_id,
            e.learner_id,
            l.name AS learner_name,
            e.course_id,
            c.title AS course_title,
            e.status AS enrollment_status,
            ra.last_activity,
            am.avg_latest_score,
            COALESCE(am.failed_attempts, 0) AS failed_attempts,
            o.completion_percentage
        FROM Enrollment e
        JOIN Learner l
            ON l.learner_id = e.learner_id
        JOIN Course c
            ON c.course_id = e.course_id
        LEFT JOIN recent_activity ra
            ON ra.enrollment_id = e.enrollment_id
        LEFT JOIN assessment_metrics am
            ON am.enrollment_id = e.enrollment_id
        LEFT JOIN CourseOutcome o
            ON o.enrollment_id = e.enrollment_id
           AND o.is_current = 1
        WHERE e.status IN ('enrolled', 'in_progress')
        ORDER BY e.learner_id, e.course_id
        """,
        (as_of.isoformat(), as_of.isoformat()),
    ).fetchall()

    learners = []

    for row in rows:
        (
            enrollment_id,
            learner_id,
            learner_name,
            course_id,
            course_title,
            enrollment_status,
            last_activity,
            avg_latest_score,
            failed_attempts,
            completion_percentage,
        ) = row

        reasons = []
        score = 0

        # No recorded activity in the configured window.
        if last_activity is None:
            reasons.append("No recorded activity")
            score += 40
        elif last_activity < cutoff.isoformat():
            reasons.append(
                f"No activity in the last {inactivity_days} days"
            )
            score += 40

        # Latest graded result for each assessment, averaged together.
        if avg_latest_score is not None and avg_latest_score < 50:
            reasons.append("Low average latest assessment score")
            score += 30

        # Repeated failures are a separate signal.
        if failed_attempts >= 2:
            reasons.append("Multiple failed assessment attempts")
            score += 20

        # Completion percentage is taken from the current outcome.
        if (
            completion_percentage is not None
            and completion_percentage < 25
        ):
            reasons.append("Low course completion progress")
            score += 20

        score = min(score, 100)

        if score >= 60:
            risk_level = "high"
            intervention = (
                "Contact learner and offer personalized support"
            )
        elif score >= 30:
            risk_level = "medium"
            intervention = (
                "Recommend learning resources and check progress"
            )
        else:
            risk_level = "low"
            intervention = "Continue routine progress monitoring"

        learners.append(
            {
                "enrollment_id": enrollment_id,
                "learner_id": learner_id,
                "learner_name": learner_name,
                "course_id": course_id,
                "course_title": course_title,
                "enrollment_status": enrollment_status,
                "last_activity": last_activity,
                "latest_assessment_average": (
                    round(avg_latest_score, 2)
                    if avg_latest_score is not None
                    else None
                ),
                "failed_attempts": failed_attempts,
                "completion_percentage": completion_percentage,
                "risk_score": score,
                "risk_level": risk_level,
                "risk_reasons": reasons,
                "recommended_intervention": intervention,
            }
        )

    return {
        "definition": (
            "Rule-based risk indicator for ongoing enrollments. "
            "It does not establish that a learner will drop out."
        ),
        "inactivity_days": inactivity_days,
        "reference_time_utc": as_of.isoformat(),
        "total_ongoing_enrollments": len(learners),
        "high_risk_enrollments": sum(
            item["risk_level"] == "high" for item in learners
        ),
        "medium_risk_enrollments": sum(
            item["risk_level"] == "medium" for item in learners
        ),
        "low_risk_enrollments": sum(
            item["risk_level"] == "low" for item in learners
        ),
        "enrollments": learners,
    }
