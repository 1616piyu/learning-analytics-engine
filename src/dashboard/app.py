
"""Portfolio-ready dashboard for the Learning Analytics Engine."""

import os
import sqlite3
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.reporting.generate_report import (  # noqa: E402
    DEFAULT_DB_PATH,
    build_report,
)

st.set_page_config(
    page_title="Learning Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- Styling --------------------

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    [data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.20);
        padding: 18px 20px;
        border-radius: 12px;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.88rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 650;
    }

    div[data-testid="stTabs"] button {
        font-weight: 600;
    }

    .dashboard-subtitle {
        color: #9CA3AF;
        font-size: 1rem;
        margin-top: -10px;
        margin-bottom: 22px;
    }

    .section-note {
        color: #9CA3AF;
        font-size: 0.88rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- Data loading --------------------


@st.cache_data(ttl=60, show_spinner=False)
def load_report(database_path, modified_time):
    """Load analytics from the existing database."""
    return build_report(database_path)


def get_database_path():
    configured_path = os.environ.get("LEARNING_ANALYTICS_DB")
    if configured_path:
        return Path(configured_path).resolve()
    return DEFAULT_DB_PATH.resolve()


database_path = get_database_path()

# -------------------- Sidebar --------------------

with st.sidebar:
    st.markdown("## 📊 Learning Analytics")
    st.caption("Dashboard controls")
    st.divider()

    if database_path.is_file():
        st.success("Database connected")
        st.caption("Database file")
        st.code(database_path.name, language=None)
    else:
        st.error("Database not found")
        st.caption("Expected location")
        st.code(str(database_path), language=None)

    if st.button("↻ Refresh analytics", use_container_width=True):
        load_report.clear()
        st.rerun()

    st.divider()
    st.caption("Data source: synthetic LMS records")
    st.caption("Analytics are read-only.")

if not database_path.is_file():
    st.error(
        "The SQLite database was not found. Generate the dataset "
        "with your existing pipeline or configure "
        "`LEARNING_ANALYTICS_DB`."
    )
    st.stop()

try:
    modified_time = database_path.stat().st_mtime
    with st.spinner("Loading learning analytics..."):
        report = load_report(str(database_path), modified_time)
except (sqlite3.Error, OSError, RuntimeError, ValueError) as exc:
    st.error("Unable to load the analytics report.")
    st.exception(exc)
    st.stop()

overview = report["overview"]
courses = pd.DataFrame(report["course_completion"])
cohorts = pd.DataFrame(report["cohort_performance"])
assessments = pd.DataFrame(report["assessment_performance"])
risk = report["learner_risk"]
risk_rows = pd.DataFrame(risk["enrollments"])
inactive = report["inactive_enrollments"]
quality = report["data_quality"]
anomalies = report["anomaly_detection"]

# -------------------- Header --------------------

st.title("Learning Analytics Dashboard")
st.markdown(
    '<p class="dashboard-subtitle">'
    "Monitor learning outcomes, compare cohorts, and identify "
    "enrollments that may need additional support."
    "</p>",
    unsafe_allow_html=True,
)

st.caption(
    "Synthetic dataset · Read-only analytics · "
    f'Reference time: {risk["reference_time_utc"]}'
)

# -------------------- KPI overview --------------------

st.subheader("Executive overview")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total learners", f'{overview["learners"]:,}')
k2.metric("Courses", f'{overview["courses"]:,}')
k3.metric("Enrollments", f'{overview["enrollments"]:,}')
completion_rate = overview["completion_rate_pct"]
k4.metric(
    "Completion rate",
    f"{completion_rate:.1f}%" if completion_rate is not None else "N/A",
)

k5, k6, k7, k8 = st.columns(4)

k5.metric("Activity events", f'{overview["activity_events"]:,}')
k6.metric("Assessment attempts", f'{overview["assessment_attempts"]:,}')
k7.metric("High-risk enrollments", f'{risk["high_risk_enrollments"]:,}')
k8.metric("Inactive enrollments", f'{inactive["inactive_enrollments"]:,}')

st.divider()

# -------------------- Tabs --------------------

overview_tab, course_tab, cohort_tab, risk_tab, quality_tab = st.tabs(
    [
        "Overview",
        "Course analytics",
        "Cohort analytics",
        "Learner risk",
        "Data quality",
    ]
)

# -------------------- Chart helpers --------------------


def horizontal_bar_chart(
    frame,
    category,
    value,
    title,
    value_label,
):
    """Render a readable horizontal bar chart."""
    chart_data = frame[[category, value]].copy()
    chart_data[value] = pd.to_numeric(
        chart_data[value], errors="coerce"
    )
    chart_data = chart_data.dropna(subset=[value])

    if chart_data.empty:
        st.info("No data is available for this chart.")
        return

    chart = (
        alt.Chart(chart_data)
        .mark_bar(
            cornerRadiusEnd=5,
            color="#60A5FA",
        )
        .encode(
            x=alt.X(
                f"{value}:Q",
                title=value_label,
                scale=alt.Scale(
                    domainMin=0,
                    nice=True,
                ),
            ),
            y=alt.Y(
                f"{category}:N",
                sort="-x",
                title=None,
                axis=alt.Axis(
                    labelLimit=240,
                    labelFontSize=12,
                ),
            ),
            tooltip=[
                alt.Tooltip(f"{category}:N", title="Name"),
                alt.Tooltip(
                    f"{value}:Q",
                    title=value_label,
                    format=".2f",
                ),
            ],
        )
        .properties(
            title=title,
            height=max(200, min(420, 34 * len(chart_data))),
        )
        .configure_view(stroke=None)
        .configure_axis(
            gridColor="rgba(128,128,128,0.18)",
            domain=False,
        )
    )

    st.altair_chart(chart, use_container_width=True)


# -------------------- Overview tab --------------------

with overview_tab:
    left, right = st.columns([1.3, 1])

    with left:
        st.subheader("Course completion")
        if not courses.empty:
            horizontal_bar_chart(
                courses,
                "course_title",
                "completion_rate_pct",
                "Completion rate by course",
                "Completion (%)",
            )
        else:
            st.info("No course completion metrics available.")

    with right:
        st.subheader("Risk distribution")

        risk_distribution = pd.DataFrame(
            [
                {
                    "Risk level": "High",
                    "Enrollments": risk["high_risk_enrollments"],
                },
                {
                    "Risk level": "Medium",
                    "Enrollments": risk["medium_risk_enrollments"],
                },
                {
                    "Risk level": "Low",
                    "Enrollments": risk["low_risk_enrollments"],
                },
            ]
        )

        risk_chart = (
            alt.Chart(risk_distribution)
            .mark_bar(
                cornerRadiusEnd=5,
                color="#60A5FA",
            )
            .encode(
                x=alt.X("Enrollments:Q", title="Enrollments"),
                y=alt.Y(
                    "Risk level:N",
                    sort=["High", "Medium", "Low"],
                    title=None,
                ),
                tooltip=["Risk level", "Enrollments"],
            )
            .properties(height=190)
            .configure_view(stroke=None)
            .configure_axis(domain=False)
        )

        st.altair_chart(risk_chart, use_container_width=True)

        st.caption(
            "Risk levels are rule-based indicators for ongoing "
            "enrollments, not confirmed dropouts."
        )

    st.subheader("Assessment performance")
    if not assessments.empty:
        horizontal_bar_chart(
            assessments,
            "course_title",
            "average_score",
            "Average graded assessment score by course",
            "Average score",
        )
    else:
        st.info("No assessment metrics available.")

# -------------------- Course tab --------------------

with course_tab:
    st.subheader("Course performance")

    if not courses.empty:
        course_filter = st.selectbox(
            "Filter course",
            ["All courses"] + sorted(
                courses["course_title"].dropna().unique().tolist()
            ),
        )

        filtered_courses = courses.copy()
        if course_filter != "All courses":
            filtered_courses = filtered_courses[
                filtered_courses["course_title"] == course_filter
            ]

        st.dataframe(
            filtered_courses,
            use_container_width=True,
            hide_index=True,
        )

        if len(filtered_courses) > 1:
            horizontal_bar_chart(
                filtered_courses,
                "course_title",
                "avg_completion_percentage",
                "Average recorded progress",
                "Progress (%)",
            )
    else:
        st.info("No course data available.")

# -------------------- Cohort tab --------------------

with cohort_tab:
    st.subheader("Cohort comparison")

    if not cohorts.empty:
        st.dataframe(
            cohorts,
            use_container_width=True,
            hide_index=True,
        )

        horizontal_bar_chart(
            cohorts,
            "cohort_name",
            "completion_rate_pct",
            "Completion rate by cohort",
            "Completion (%)",
        )
    else:
        st.info("No cohort metrics available.")

# -------------------- Risk tab --------------------

with risk_tab:
    st.subheader("Learner risk explorer")

    st.markdown(
        '<p class="section-note">'
        "Use risk signals to prioritize support. A risk score is "
        "not a prediction of learner dropout."
        "</p>",
        unsafe_allow_html=True,
    )

    r1, r2, r3 = st.columns(3)
    r1.metric("High risk", risk["high_risk_enrollments"])
    r2.metric("Medium risk", risk["medium_risk_enrollments"])
    r3.metric("Low risk", risk["low_risk_enrollments"])

    if not risk_rows.empty:
        filter_col, search_col = st.columns([1, 2])

        with filter_col:
            selected_level = st.selectbox(
                "Risk level",
                ["All", "high", "medium", "low"],
            )

        with search_col:
            search_text = st.text_input(
                "Search learner or course",
                placeholder="Enter a learner ID, name, or course...",
            )

        filtered = risk_rows.copy()

        if selected_level != "All":
            filtered = filtered[
                filtered["risk_level"] == selected_level
            ]

        if search_text.strip():
            term = search_text.strip()
            matches = (
                filtered["learner_id"].astype(str).str.contains(
                    term, case=False, na=False
                )
                | filtered["learner_name"].astype(str).str.contains(
                    term, case=False, na=False
                )
                | filtered["course_title"].astype(str).str.contains(
                    term, case=False, na=False
                )
            )
            filtered = filtered[matches]

        display_columns = [
            "learner_id",
            "learner_name",
            "course_title",
            "risk_score",
            "risk_level",
            "risk_reasons",
            "recommended_intervention",
        ]

        st.caption(f"{len(filtered):,} matching enrollments")
        st.dataframe(
            filtered[display_columns],
            use_container_width=True,
            hide_index=True,
        )

        if not filtered.empty:
            selected_enrollment = st.selectbox(
                "Inspect enrollment details",
                filtered["enrollment_id"].tolist(),
            )
            record = filtered[
                filtered["enrollment_id"] == selected_enrollment
            ].iloc[0]

            st.markdown("#### Risk assessment")

            a, b = st.columns(2)
            a.metric("Risk score", f'{record["risk_score"]} / 100')
            b.metric("Risk level", str(record["risk_level"]).upper())

            st.write(
                f'**Learner:** {record["learner_name"]} '
                f'({record["learner_id"]})'
            )
            st.write(f'**Course:** {record["course_title"]}')

            st.write("**Contributing signals**")
            if record["risk_reasons"]:
                for reason in record["risk_reasons"]:
                    st.write(f"- {reason}")
            else:
                st.write("No configured risk signals were detected.")

            st.info(
                "Suggested intervention: "
                + str(record["recommended_intervention"])
            )
    else:
        st.info("No ongoing enrollments are available for risk analysis.")

# -------------------- Data quality tab --------------------

with quality_tab:
    st.subheader("Data quality")

    q1, q2, q3, q4 = st.columns(4)

    q1.metric("Checks run", quality["checks_run"])
    q2.metric("Passed", quality["passed_checks"])
    q3.metric("Warnings", quality["warning_checks"])
    q4.metric("Failed", quality["failed_checks"])

    checks = pd.DataFrame(quality["checks"])
    if not checks.empty:
        st.dataframe(
            checks,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    st.subheader("Anomaly detection")

    a1, a2 = st.columns(2)
    a1.metric("Total findings", anomalies["total_findings"])
    a2.metric(
        "Detection status",
        anomalies["status"].replace("_", " ").title(),
    )

    issue_counts = anomalies["findings_by_type"]

    if issue_counts:
        findings = pd.DataFrame(
            [
                {"Issue type": issue, "Count": count}
                for issue, count in issue_counts.items()
            ]
        )
        st.dataframe(
            findings,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("No anomaly findings were reported.")

st.divider()
st.caption(
    "Learning Analytics Engine · Python · SQLite · Streamlit"
)
