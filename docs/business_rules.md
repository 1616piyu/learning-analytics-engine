
# Business Rules

1. Generate parent/master records before dependent records.
2. Every normal enrollment must reference an existing learner and course.
3. Every valid activity event must reference an enrollment.
4. Deduplicate events before calculating engagement.
5. Preserve event time and ingestion time separately.
6. Normalize event timestamps to UTC before assigning reporting weeks.
7. Count a learner as weekly active if they have at least one qualifying valid event during the reporting week.
8. Mark a course completed only when its effective completion rule is satisfied.
9. Required assessments must be passed according to the course's rule.
10. Retain assessment attempts as separate historical records.
11. Preserve anomaly records and record the reason for every exception.
12. Keep ground-truth labels separate from analytical input data.
13. Use a fixed random seed for reproducible generation.
14. Compare cohorts over consistent reporting windows.
