

\# Entity Relationship Diagram



The diagram below summarizes the main entities in the Learning Analytics Engine and their relationships.



```mermaid

erDiagram

&#x20;   LEARNER ||--o{ ENROLLMENT : has

&#x20;   COURSE ||--o{ ENROLLMENT : includes

&#x20;   LEARNER ||--o{ LEARNER\_COHORT : joins

&#x20;   COHORT ||--o{ LEARNER\_COHORT : contains

&#x20;   COURSE ||--o{ CONTENT\_ITEM : contains

&#x20;   CONTENT\_ITEM o|--o{ CONTENT\_ITEM : parent\_of

&#x20;   COURSE ||--o{ ASSESSMENT : has

&#x20;   COURSE ||--o{ COMPLETION\_RULE : defines

&#x20;   ENROLLMENT ||--o{ ACTIVITY\_EVENT : generates

&#x20;   CONTENT\_ITEM ||--o{ ACTIVITY\_EVENT : relates\_to

&#x20;   ENROLLMENT ||--o{ ATTEMPT : makes

&#x20;   ASSESSMENT ||--o{ ATTEMPT : receives

&#x20;   ENROLLMENT ||--o{ COURSE\_OUTCOME : produces

&#x20;   COMPLETION\_RULE ||--o{ COURSE\_OUTCOME : governs

```



\## Main entities



\- \*\*Learner:\*\* learner profile and account status.

\- \*\*Course:\*\* course metadata and publication status.

\- \*\*Cohort:\*\* learner grouping.

\- \*\*LearnerCohort:\*\* membership linking learners and cohorts.

\- \*\*ContentItem:\*\* course content organized by sequence and optional parent item.

\- \*\*Assessment:\*\* course assessments and passing requirements.

\- \*\*CompletionRule:\*\* versioned rules used to evaluate course completion.

\- \*\*Enrollment:\*\* a learner's registration in a course.

\- \*\*ActivityEvent:\*\* recorded learner interactions with course content.

\- \*\*Attempt:\*\* an assessment attempt and its result.

\- \*\*CourseOutcome:\*\* calculated course progress and completion status.



The database schema in `src/database/schema.sql` is the authoritative source for exact columns, keys, constraints, and relationship cardinalities.
