
-- Course completion metrics by course.
-- Only the current outcome record is counted for each enrollment.

SELECT
    en.course_id,

    COUNT(DISTINCT en.enrollment_id) AS total_enrollments,

    COUNT(DISTINCT CASE
        WHEN o.outcome_status = 'completed'
        THEN en.enrollment_id
    END) AS completed_enrollments,

    ROUND(
        100.0 * COUNT(DISTINCT CASE
            WHEN o.outcome_status = 'completed'
            THEN en.enrollment_id
        END)
        / NULLIF(COUNT(DISTINCT en.enrollment_id), 0),
        2
    ) AS completion_rate_pct,

    ROUND(AVG(o.completion_percentage), 2)
        AS avg_completion_percentage

FROM Enrollment en

LEFT JOIN CourseOutcome o
    ON o.enrollment_id = en.enrollment_id
   AND o.is_current = 1

GROUP BY en.course_id
ORDER BY completion_rate_pct DESC;
