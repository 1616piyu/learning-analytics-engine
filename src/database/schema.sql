
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Learner (
    learner_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('active', 'inactive', 'suspended'))
);

CREATE TABLE IF NOT EXISTS Course (
    course_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('draft', 'published', 'archived')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Cohort (
    cohort_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    description TEXT,
    CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS LearnerCohort (
    learner_id TEXT NOT NULL REFERENCES Learner(learner_id),
    cohort_id TEXT NOT NULL REFERENCES Cohort(cohort_id),
    joined_at TEXT NOT NULL,
    left_at TEXT,
    PRIMARY KEY (learner_id, cohort_id, joined_at),
    CHECK (left_at IS NULL OR left_at >= joined_at)
);

CREATE TABLE IF NOT EXISTS Enrollment (
    enrollment_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL REFERENCES Learner(learner_id),
    course_id TEXT NOT NULL REFERENCES Course(course_id),
    enrolled_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('enrolled', 'in_progress', 'completed', 'withdrawn')
    ),
    UNIQUE (learner_id, course_id)
);

CREATE TABLE IF NOT EXISTS ContentItem (
    content_id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL REFERENCES Course(course_id),
    parent_content_id TEXT REFERENCES ContentItem(content_id),
    title TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (
        content_type IN ('module', 'video', 'reading', 'quiz')
    ),
    sequence_number INTEGER NOT NULL CHECK (sequence_number >= 0),
    is_required INTEGER NOT NULL CHECK (is_required IN (0, 1)),
    UNIQUE (course_id, sequence_number)
);

CREATE TABLE IF NOT EXISTS Assessment (
    assessment_id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL REFERENCES Course(course_id),
    title TEXT NOT NULL,
    passing_score REAL NOT NULL CHECK (passing_score BETWEEN 0 AND 100),
    is_required INTEGER NOT NULL CHECK (is_required IN (0, 1))
);

CREATE TABLE IF NOT EXISTS CompletionRule (
    rule_id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL REFERENCES Course(course_id),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    required_content_count INTEGER NOT NULL
        CHECK (required_content_count >= 0),
    require_assessment_pass INTEGER NOT NULL
        CHECK (require_assessment_pass IN (0, 1)),
    rule_version INTEGER NOT NULL CHECK (rule_version > 0),
    CHECK (effective_to IS NULL OR effective_to >= effective_from),
    UNIQUE (course_id, rule_version)
);

CREATE TABLE IF NOT EXISTS ActivityEvent (
    event_id TEXT PRIMARY KEY,
    enrollment_id TEXT REFERENCES Enrollment(enrollment_id),
    content_id TEXT REFERENCES ContentItem(content_id),
    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'content_opened',
            'content_completed',
            'video_progress',
            'assessment_started',
            'assessment_submitted'
        )
    ),
    event_time TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    source_event_id TEXT,
    device_type TEXT NOT NULL CHECK (
        device_type IN ('web', 'mobile', 'offline_sync')
    ),
    issue_type TEXT
);

CREATE TABLE IF NOT EXISTS Attempt (
    attempt_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL REFERENCES Enrollment(enrollment_id),
    assessment_id TEXT NOT NULL REFERENCES Assessment(assessment_id),
    attempt_number INTEGER NOT NULL CHECK (attempt_number > 0),
    score REAL CHECK (score IS NULL OR score BETWEEN 0 AND 100),
    started_at TEXT NOT NULL,
    submitted_at TEXT,
    status TEXT NOT NULL CHECK (
        status IN ('in_progress', 'submitted', 'graded', 'invalid')
    ),
    UNIQUE (enrollment_id, assessment_id, attempt_number),
    CHECK (submitted_at IS NULL OR submitted_at >= started_at)
);

CREATE TABLE IF NOT EXISTS CourseOutcome (
    outcome_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL REFERENCES Enrollment(enrollment_id),
    calculated_at TEXT NOT NULL,
    outcome_status TEXT NOT NULL CHECK (
        outcome_status IN ('not_started', 'in_progress', 'completed', 'at_risk')
    ),
    completion_percentage REAL NOT NULL
        CHECK (completion_percentage BETWEEN 0 AND 100),
    rule_id TEXT NOT NULL REFERENCES CompletionRule(rule_id),
    is_current INTEGER NOT NULL CHECK (is_current IN (0, 1)),
    UNIQUE (enrollment_id, calculated_at)
);

CREATE INDEX IF NOT EXISTS idx_enrollment_learner
    ON Enrollment(learner_id);

CREATE INDEX IF NOT EXISTS idx_enrollment_course
    ON Enrollment(course_id);

CREATE INDEX IF NOT EXISTS idx_event_enrollment_time
    ON ActivityEvent(enrollment_id, event_time);

CREATE INDEX IF NOT EXISTS idx_attempt_enrollment
    ON Attempt(enrollment_id);

CREATE INDEX IF NOT EXISTS idx_outcome_enrollment
    ON CourseOutcome(enrollment_id);
