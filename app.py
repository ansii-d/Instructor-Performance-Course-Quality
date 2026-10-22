from pathlib import Path
import sys

# Dynamically add project root to python path for src module resolution
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

import numpy as np
import pandas as pd
import streamlit as st

# Import backend modules matching your exact filenames in src/
from src.analysis import (
    add_rating_tiers,
    course_quality_summary,
    experience_correlations,
    expertise_summary,
    instructor_summary,
)
from src.data_cleaning import (
    clean_courses,
    clean_teachers,
    clean_transactions,
    create_master_dataset,
    data_quality_report,
)
from src.data_loader import load_raw_data
from src.kpis import calculate_kpis
from src.visualizations import (
    category_bar,
    experience_scatter,
    expertise_bar,
    heatmap_figure,
)

st.set_page_config(
    page_title="EduPro: Instructor & Course Quality Evaluation",
    page_icon="🎓",
    layout="wide",
)


@st.cache_data
def load_and_process_data():
    raw_dir = project_root / "data" / "raw"

    # Use data_loader module to load raw data or generate mock datasets
    teachers_df, courses_df, transactions_df = load_raw_data(raw_dir)

    # Clean datasets using data_cleaning pipeline
    teachers_clean = clean_teachers(teachers_df)
    courses_clean = clean_courses(courses_df)
    transactions_clean = clean_transactions(transactions_df)

    master = create_master_dataset(
        teachers_clean, courses_clean, transactions_clean
    )
    dq_report = data_quality_report(
        teachers_clean, courses_clean, transactions_clean, master
    )
    instructor_stats = instructor_summary(
        teachers_clean, courses_clean, transactions_clean
    )
    instructor_tiered = add_rating_tiers(instructor_stats)
    kpis = calculate_kpis(
        teachers_clean, courses_clean, transactions_clean, instructor_tiered
    )

    return (
        teachers_clean,
        courses_clean,
        transactions_clean,
        master,
        dq_report,
        instructor_tiered,
        kpis,
    )


(
    teachers_df,
    courses_df,
    transactions_df,
    master_df,
    dq_report,
    instructor_stats,
    project_kpis,
) = load_and_process_data()

# --- Sidebar Controls ---
st.sidebar.header("🎓 EduPro Control Panel")

uploaded_teachers = st.sidebar.file_uploader(
    "Upload Teachers CSV", type=["csv"]
)
uploaded_courses = st.sidebar.file_uploader("Upload Courses CSV", type=["csv"])
uploaded_transactions = st.sidebar.file_uploader(
    "Upload Transactions CSV", type=["csv"]
)

if uploaded_teachers and uploaded_courses and uploaded_transactions:
    teachers_df = clean_teachers(pd.read_csv(uploaded_teachers))
    courses_df = clean_courses(pd.read_csv(uploaded_courses))
    transactions_df = clean_transactions(pd.read_csv(uploaded_transactions))
    master_df = create_master_dataset(teachers_df, courses_df, transactions_df)
    dq_report = data_quality_report(
        teachers_df, courses_df, transactions_df, master_df
    )
    instructor_stats = add_rating_tiers(
        instructor_summary(teachers_df, courses_df, transactions_df)
    )
    project_kpis = calculate_kpis(
        teachers_df, courses_df, transactions_df, instructor_stats
    )

st.sidebar.markdown("---")
selected_expertise = st.sidebar.multiselect(
    "Filter by Expertise",
    options=teachers_df["Expertise"].dropna().unique().tolist(),
    default=teachers_df["Expertise"].dropna().unique().tolist(),
)

selected_category = st.sidebar.multiselect(
    "Filter by Course Category",
    options=courses_df["CourseCategory"].dropna().unique().tolist(),
    default=courses_df["CourseCategory"].dropna().unique().tolist(),
)

selected_level = st.sidebar.multiselect(
    "Filter by Course Level",
    options=courses_df["CourseLevel"].dropna().unique().tolist(),
    default=courses_df["CourseLevel"].dropna().unique().tolist(),
)

min_rating, max_rating = st.sidebar.slider(
    "Teacher Rating Range",
    float(teachers_df["TeacherRating"].min()),
    float(teachers_df["TeacherRating"].max()),
    (
        float(teachers_df["TeacherRating"].min()),
        float(teachers_df["TeacherRating"].max()),
    ),
)

# Apply Filters
filtered_instructors = instructor_stats[
    (instructor_stats["Expertise"].isin(selected_expertise))
    & (instructor_stats["TeacherRating"] >= min_rating)
    & (instructor_stats["TeacherRating"] <= max_rating)
]

filtered_courses = courses_df[
    (courses_df["CourseCategory"].isin(selected_category))
    & (courses_df["CourseLevel"].isin(selected_level))
]

# --- Main Dashboard ---
st.title("📊 EduPro: Instructor Performance & Course Quality Dashboard")
st.markdown(
    "A data-driven framework evaluating instructor effectiveness, teaching tenure impact, and course quality consistency across the platform."
)
st.markdown("---")

# Top-level Metric Cards using calculate_kpis() dictionary
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Average Teacher Rating",
    f"{project_kpis.get('Average teacher rating', 0):.2f} ⭐",
)
col2.metric(
    "Average Course Rating",
    f"{project_kpis.get('Average course rating', 0):.2f} ⭐",
)
col3.metric("Active Instructors", f"{project_kpis.get('Instructor count', 0)}")
col4.metric(
    "Total Transactions", f"{project_kpis.get('Transaction count', 0):,}"
)

st.markdown("---")

# Core Modules / Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Instructor Leaderboard",
    "📈 Experience vs Rating",
    "🗺️ Course Quality & Heatmaps",
    "💡 Expertise Insights",
    "🔍 Data Quality Audit",
])

with tab1:
    st.subheader("Instructor Performance Leaderboard")
    display_cols = [
        "TeacherID",
        "TeacherName",
        "Expertise",
        "YearsOfExperience",
        "TeacherRating",
        "AssociatedCourseCount",
        "MeanAssociatedCourseRating",
        "TransactionCount",
        "RatingTier",
    ]
    st.dataframe(
        filtered_instructors[display_cols].sort_values(
            by="TeacherRating", ascending=False
        ),
        width="stretch",
    )

with tab2:
    st.subheader("Instructor Experience vs Ratings")
    fig_exp = experience_scatter(filtered_instructors)
    st.plotly_chart(fig_exp, use_container_width=True)

    st.markdown("##### Statistical Correlation Summary")
    corrs = experience_correlations(teachers_df, instructor_stats)
    corr_df = pd.DataFrame([
        {
            "Metric Pair": k,
            "Coefficient": v["coefficient"],
            "p-value": v["p_value"],
            "n": v["n"],
        }
        for k, v in corrs.items()
    ])
    st.dataframe(corr_df, width="stretch")

with tab3:
    st.subheader("Course Quality Breakdown & Heatmaps")
    cat_summary, level_summary, heatmap_pivot = course_quality_summary(
        filtered_courses
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### Category-wise Quality")
        st.dataframe(cat_summary, width="stretch")
        st.plotly_chart(category_bar(cat_summary), use_container_width=True)

    with col_b:
        st.markdown("##### Level-wise Quality")
        st.dataframe(level_summary, width="stretch")

    st.markdown("##### Course Rating Heatmap (Category × Level)")
    st.plotly_chart(heatmap_figure(heatmap_pivot), use_container_width=True)

with tab4:
    st.subheader("Expertise-Based Performance Insights")
    exp_sum = expertise_summary(
        teachers_df[teachers_df["Expertise"].isin(selected_expertise)]
    )
    st.dataframe(exp_sum, width="stretch")
    st.plotly_chart(expertise_bar(exp_sum), use_container_width=True)

with tab5:
    st.subheader("Data Quality Audit Report")
    st.json(dq_report)
    st.markdown("##### Master Dataset Preview")
    st.dataframe(master_df.head(100), width="stretch")