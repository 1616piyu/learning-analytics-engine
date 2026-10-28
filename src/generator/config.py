
from datetime import datetime, timezone

# Fixed seed used throughout the synthetic data pipeline
SEED = 20261022

# Fixed reference time so generated timestamps don't change between runs
REFERENCE_TIME = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
