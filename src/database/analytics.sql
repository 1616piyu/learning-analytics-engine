
-- Weekly learner engagement metrics.
-- Normalize ISO timestamps to UTC before grouping by week.

WITH normalized_events AS (
    SELECT
        e.event_id,
        e.enrollment_id,
        en.learner_id,
        en.course_id,
        e.event_time,

        strftime(
            '%Y-%W',
            CASE
                WHEN substr(e.event_time, -1) = 'Z'
                    THEN e.event_time
                WHEN substr(e.event_time, 20, 1) IN ('+', '-')
                    THEN datetime(e.event_time)
                ELSE e.event_time
            END
        ) AS activity_week

    FROM ActivityEvent e
    JOIN Enrollment en
        ON e.enrollment_id = en.enrollment_id

    WHERE e.event_time IS NOT NULL
)

SELECT
    activity_week,
    COUNT(DISTINCT learner_id) AS active_learners,
    COUNT(*) AS total_events,
    COUNT(DISTINCT enrollment_id) AS active_enrollments,
    COUNT(DISTINCT course_id) AS courses_with_activity

FROM normalized_events

GROUP BY activity_week
ORDER BY activity_week;
