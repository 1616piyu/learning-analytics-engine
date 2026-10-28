"""Business analytics for learner cohorts and inactivity."""

from datetime import timedelta

from src.generator.config import REFERENCE_TIME


def get_cohort_performance(conn):
    """Calculate learner and completion metrics for each cohort."""
    rows = conn.execute("""
        SELECT
            c.cohort_id,
            c.name AS cohort_name,
            COUNT(DISTINCT lc.learner_id) AS learners,
            COUNT(DISTINCT e.enrollment_id) AS enrollments,
            COUNT(DISTINCT CASE
                WHEN o.outcome_status = 'completed'
                THEN e.enrollment_id
            END) AS completed_enrollments,
            ROUND(
                100.0 * COUNT(DISTINCT CASE
                    WHEN o.outcome_status = 'completed'
                    THEN e.enrollment_id
                END) / NULLIF(COUNT(DISTINCT e.enrollment_id), 0),
                2
            ) AS completion_rate_pct
        FROM Cohort c
        LEFT JOIN LearnerCohort lc
            ON lc.cohort_id = c.cohort_id
        LEFT JOIN Enrollment e
            ON e.learner_id = lc.learner_id
        LEFT JOIN CourseOutcome o
            ON o.enrollment_id = e.enrollment_id
           AND o.is_current = 1
        GROUP BY c.cohort_id, c.name
        ORDER BY c.cohort_id
    """).fetchall()

    columns = [
        "cohort_id",
        "cohort_name",
        "learners",
        "enrollments",
        "completed_enrollments",
        "completion_rate_pct",
    ]

    return [dict(zip(columns, row)) for row in rows]


def get_inactive_enrollment_metrics(conn, inactivity_days=30):
    """
    Summarize ongoing enrollments with no recent recorded activity.

    The cutoff is based on the fixed synthetic reference timestamp,
    so repeated runs produce consistent results.
    Completed and withdrawn enrollments are excluded.
    """
    if not isinstance(inactivity_days, int) or inactivity_days < 1:
        raise ValueError("inactivity_days must be a positive integer")

    as_of = REFERENCE_TIME
    cutoff = as_of - timedelta(days=inactivity_days)

    rows = conn.execute("""
        SELECT
            c.course_id,
            c.title AS course_title,
            COUNT(e.enrollment_id) AS ongoing_enrollments,
            SUM(CASE
                WHEN recent_activity.enrollment_id IS NULL THEN 1
                ELSE 0
            END) AS inactive_enrollments,
            ROUND(
                100.0 * SUM(CASE
                    WHEN recent_activity.enrollment_id IS NULL THEN 1
                    ELSE 0
                END) / NULLIF(COUNT(e.enrollment_id), 0),
                2
            ) AS inactivity_rate_pct
        FROM Course c
        LEFT JOIN Enrollment e
            ON e.course_id = c.course_id
           AND e.status IN ('enrolled', 'in_progress')
        LEFT JOIN (
            SELECT DISTINCT enrollment_id
            FROM ActivityEvent
            WHERE enrollment_id IS NOT NULL
              AND datetime(event_time) >= datetime(?)
              AND datetime(event_time) <= datetime(?)
        ) recent_activity
            ON recent_activity.enrollment_id = e.enrollment_id
        GROUP BY c.course_id, c.title
        ORDER BY c.title
    """, (cutoff.isoformat(), as_of.isoformat())).fetchall()

    columns = [
        "course_id",
        "course_title",
        "ongoing_enrollments",
        "inactive_enrollments",
        "inactivity_rate_pct",
    ]

    course_metrics = [dict(zip(columns, row)) for row in rows]

    return {
        "definition": (
            "An enrolled or in-progress enrollment with no recorded "
            f"activity in the {inactivity_days} days before the "
            "reference timestamp. This indicates inactivity, not "
            "confirmed dropout."
        ),
        "inactivity_days": inactivity_days,
        "reference_time_utc": as_of.isoformat(),
        "cutoff_time_utc": cutoff.isoformat(),
        "ongoing_enrollments": sum(
            row["ongoing_enrollments"] for row in course_metrics
        ),
        "inactive_enrollments": sum(
            row["inactive_enrollments"] for row in course_metrics
        ),
        "courses": course_metrics,
    }
