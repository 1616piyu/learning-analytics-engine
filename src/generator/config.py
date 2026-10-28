
from datetime import datetime, timezone

# Fixed seed: every generation run must be reproducible.
SEED = 20261022
REFERENCE_TIME = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)

SCALE_PROFILES = {
    "starter": {
        "learners": 100,
        "courses": 10,
        "cohorts": 4,
        "enrollments": None,  # Preserve the existing randomized 3–5 range.
        "activity_events": None,  # Preserve the existing natural event count.
    },
    "full": {
        "learners": 20_000,
        "courses": 500,
        "cohorts": 20,
        "enrollments": 100_000,
        "activity_events": 2_000_000,
    },
}
