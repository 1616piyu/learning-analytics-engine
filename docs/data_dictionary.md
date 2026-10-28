
# Data Dictionary

## 1. Learner
- learner_id: STRING, primary key, format LRN-000001
- name: STRING, required, synthetic name
- email: STRING, unique, synthetic email
- created_at: DATETIME, required
- status: ENUM(active, inactive, suspended)

## 2. Course
- course_id: STRING, primary key, format CRS-000001
- title: STRING, required
- category: STRING, required
- status: ENUM(draft, published, archived)
- created_at: DATETIME, required

## 3. Enrollment
- enrollment_id: STRING, primary key
- learner_id: STRING, FK -> Learner
- course_id: STRING, FK -> Course
- enrolled_at: DATETIME, required
- status: ENUM(enrolled, in_progress, completed, withdrawn)

## 4. ContentItem
- content_id: STRING, primary key
- course_id: STRING, FK -> Course
- parent_content_id: STRING, optional self-referencing FK
- title: STRING, required
- content_type: ENUM(module, video, reading, quiz)
- sequence_number: INTEGER, non-negative
- is_required: BOOLEAN

## 5. ActivityEvent
- event_id: STRING, primary key
- enrollment_id: STRING, nullable for deliberate invalid-enrollment cases
- content_id: STRING, optional FK -> ContentItem
- event_type: ENUM(content_opened, content_completed, video_progress, assessment_started, assessment_submitted)
- event_time: DATETIME, required; UTC
- ingested_at: DATETIME, required; UTC
- source_event_id: STRING, optional; identifies the original offline event
- device_type: ENUM(web, mobile, offline_sync)
- issue_type: STRING, optional; anomaly classification

## 6. Assessment
- assessment_id: STRING, primary key, format ASM-2026-000001
- course_id: STRING, FK -> Course
- title: STRING, required
- passing_score: REAL, range 0-100
- is_required: BOOLEAN

## 7. Attempt
- attempt_id: STRING, primary key
- enrollment_id: STRING, FK -> Enrollment
- assessment_id: STRING, FK -> Assessment
- attempt_number: INTEGER, positive
- score: REAL, range 0-100, nullable before grading
- started_at: DATETIME, required
- submitted_at: DATETIME, optional
- status: ENUM(in_progress, submitted, graded, invalid)

## 8. CompletionRule
- rule_id: STRING, primary key
- course_id: STRING, FK -> Course
- effective_from: DATETIME, required
- effective_to: DATETIME, optional
- required_content_count: INTEGER, non-negative
- require_assessment_pass: BOOLEAN
- rule_version: INTEGER, positive

## 9. Cohort
- cohort_id: STRING, primary key
- name: STRING, required
- start_date: DATE, required
- end_date: DATE, optional
- description: STRING, optional

## 10. CourseOutcome
- outcome_id: STRING, primary key
- enrollment_id: STRING, FK -> Enrollment
- calculated_at: DATETIME, required
- outcome_status: ENUM(not_started, in_progress, completed, at_risk)
- completion_percentage: REAL, range 0-100
- rule_id: STRING, FK -> CompletionRule
- is_current: BOOLEAN

## Supporting bridge table: LearnerCohort
- learner_id: STRING, FK -> Learner
- cohort_id: STRING, FK -> Cohort
- joined_at: DATETIME, required
- left_at: DATETIME, optional
- Composite primary key: learner_id, cohort_id, joined_at

## Data Quality and Validation Notes

- Primary keys must be unique and non-null.
- Foreign keys must reference existing records, except where a relationship
  is explicitly optional.
- Enum values must match the allowed values documented for each field.
- Date and timestamp fields must follow the documented ordering and
  lifecycle rules.
- Scores and completion percentages must remain within their documented
  ranges.
- Activity events with missing or invalid enrollment associations are treated
  as data-quality cases, not silently assumed to be valid learner activity.
- Completion eligibility must be evaluated against the applicable
  completion rule and required assessment results.
- Cohort comparisons must use consistent reporting windows.
- Timestamps used for cross-system comparisons must have clearly defined
  timezone handling.