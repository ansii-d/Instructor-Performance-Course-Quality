from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st



PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Resolve the project root whether this file is in the project root or src/.
APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent if APP_DIR.name == "src" else APP_DIR
if not (ROOT / "src").is_dir() and (APP_DIR.parent / "src").is_dir():
    ROOT = APP_DIR.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_all_data
from src.data_cleaning import (
    clean_teachers,
    clean_courses,
    clean_transactions,
    create_master_dataset,
    data_quality_report,
    save_processed_data,
)
from src.analysis import (
    instructor_summary,
    experience_correlations,
    add_rating_tiers,
    expertise_summary,
    course_quality_summary,
)
from src.kpis import calculate_kpis
from src.visualizations import (
    experience_scatter,
    expertise_bar,
    category_bar,
    heatmap_figure,
)

st.set_page_config(
    page_title="EduPro Evaluation",
    page_icon="🎓",
    layout="wide",
)

st.title("EduPro Instructor Performance & Course Quality")
st.caption(
    "Instructor effectiveness | Course quality | Experience | "
    "Expertise | Transaction demand"
)


def save_dashboard_outputs(

        master,
        quality,
        stats,
        expertise,
        category,
        level,
        pivot,
        kpis,
        correlations,
        
    
):
    """Save dashboard datasets, summaries, KPIs, and validation reports."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    # Main datasets and analysis tables
    master.to_csv(OUTPUTS_DIR / "master_dataset.csv", index=False)
    stats.to_csv(OUTPUTS_DIR / "instructor_summary.csv", index=False)
    expertise.to_csv(OUTPUTS_DIR / "expertise_summary.csv", index=False)
    category.to_csv(OUTPUTS_DIR / "course_category_summary.csv", index=False)
    level.to_csv(OUTPUTS_DIR / "course_level_summary.csv", index=False)
    pivot.to_csv(OUTPUTS_DIR / "course_rating_pivot.csv")

    # KPIs and data quality report
    pd.DataFrame([kpis]).to_csv(
        OUTPUTS_DIR / "dashboard_kpis.csv", index=False
    )
    pd.DataFrame([quality]).to_csv(
        OUTPUTS_DIR / "data_quality_report.csv", index=False
    )

    # Experience correlation analysis
    correlation_rows = [
        {"Analysis": name, **result}
        for name, result in correlations.items()
    ]
    pd.DataFrame(correlation_rows).to_csv(
        OUTPUTS_DIR / "experience_correlations.csv", index=False
    )


@st.cache_data(show_spinner="Loading and preparing EduPro data...")
def prepare_data():
    """Load, clean, validate, and summarize the dashboard data."""
    teachers, courses, transactions = load_all_data()

    teachers = clean_teachers(teachers)
    courses = clean_courses(courses)
    transactions = clean_transactions(transactions)

    master = create_master_dataset(teachers, courses, transactions)

    # Persist the cleaned tables and joined dataset in data/processed/.
    # save_processed_data should create the directory if it does not exist.
    save_processed_data(teachers, courses, transactions, master)

    quality = data_quality_report(teachers, courses, transactions, master)
    stats = instructor_summary(teachers, courses, transactions)
    expertise = expertise_summary(teachers)
    category, level, pivot = course_quality_summary(courses)
    kpis = calculate_kpis(teachers, courses, transactions, stats)
    correlations = experience_correlations(teachers, stats)

    save_dashboard_outputs(
    master,
    quality,
    stats,
    expertise,
    category,
    level,
    pivot,
    kpis,
    correlations,
) 
    return (
        teachers,
        courses,
        transactions,
        master,
        quality,
        stats,
        expertise,
        category,
        level,
        pivot,
        kpis,
        correlations,
    )


try:
    (
        teachers,
        courses,
        transactions,
        master,
        quality,
        stats,
        expertise,
        category,
        level,
        pivot,
        kpis,
        correlations,
    ) = prepare_data()
except Exception as error:
    st.error(f"Unable to load or prepare the dashboard data: {error}")
    st.markdown(
        """
        **Check the following:**
        - The source CSV files exist in `data/raw/`.
        - The filenames and required column names match `src/data_loader.py`
          and `src/data_cleaning.py`.
        - The `src` folder is in the project root and contains the imported
          modules.
        - `save_processed_data()` is defined in `src/data_cleaning.py`.
        """
    )
    st.stop()


# Sidebar filters
with st.sidebar:
    st.header("Dashboard Filters")

    expertise_options = (
        sorted(teachers["Expertise"].dropna().astype(str).unique().tolist())
        if "Expertise" in teachers.columns
        else []
    )
    selected_expertise = st.multiselect(
        "Instructor expertise",
        options=expertise_options,
        default=expertise_options,
    )

    category_options = (
        sorted(courses["CourseCategory"].dropna().astype(str).unique().tolist())
        if "CourseCategory" in courses.columns
        else []
    )
    selected_categories = st.multiselect(
        "Course category",
        options=category_options,
        default=category_options,
    )

    level_options = (
        sorted(courses["CourseLevel"].dropna().astype(str).unique().tolist())
        if "CourseLevel" in courses.columns
        else []
    )
    selected_levels = st.multiselect(
        "Course level",
        options=level_options,
        default=level_options,
    )

    rating_range = st.slider(
        "Teacher rating range",
        min_value=0.0,
        max_value=5.0,
        value=(0.0, 5.0),
        step=0.1,
    )

if "Expertise" in teachers.columns:
    expertise_mask = teachers["Expertise"].astype(str).isin(selected_expertise)
else:
    expertise_mask = pd.Series(False, index=teachers.index)

if "TeacherRating" in teachers.columns:
    rating_mask = pd.to_numeric(
        teachers["TeacherRating"], errors="coerce"
    ).between(rating_range[0], rating_range[1])
else:
    rating_mask = pd.Series(True, index=teachers.index)

filtered_teachers = teachers.loc[expertise_mask & rating_mask].copy()

if {"CourseCategory", "CourseLevel"}.issubset(courses.columns):
    filtered_courses = courses[
        courses["CourseCategory"].astype(str).isin(selected_categories)
        & courses["CourseLevel"].astype(str).isin(selected_levels)
    ].copy()
else:
    filtered_courses = courses.iloc[0:0].copy()

if "TeacherID" in stats.columns and "TeacherID" in filtered_teachers.columns:
    filtered_stats = stats[
        stats["TeacherID"].isin(filtered_teachers["TeacherID"])
    ].copy()
else:
    filtered_stats = stats.iloc[0:0].copy()


# Dashboard navigation
tabs = st.tabs(
    [
        "Overview",
        "Instructor Performance",
        "Experience Analysis",
        "Course Quality",
        "Expertise Analysis",
        "Enrollment & Data Quality",
    ]
)


# TAB 1: Overview
with tabs[0]:
    st.subheader("Executive Overview")

    metric_columns = st.columns(4)
    metric_columns[0].metric("Instructors", f"{kpis['Instructor count']:,}")
    metric_columns[1].metric("Courses", f"{kpis['Course count']:,}")
    metric_columns[2].metric("Transactions", f"{kpis['Transaction count']:,}")
    metric_columns[3].metric(
        "Average Teacher Rating",
        f"{kpis['Average teacher rating']:.2f}/5",
    )

    secondary_columns = st.columns(3)
    secondary_columns[0].metric(
        "Average Course Rating",
        f"{kpis['Average course rating']:.2f}/5",
    )
    secondary_columns[1].metric(
        "Average Experience",
        f"{kpis['Average experience (years)']:.2f} years",
    )
    secondary_columns[2].metric(
        "Rating Consistency Index",
        f"{kpis['Rating consistency index']:.3f}",
    )

    st.subheader("Experience and Instructor Rating")
    if filtered_teachers.empty:
        st.info("No instructors match the selected filters.")
    else:
        st.plotly_chart(
            experience_scatter(filtered_teachers),
            width="stretch",
            config={"displayModeBar": True, "responsive": True},
            key="tab0_experience_scatter",
        )

    st.subheader("Data Quality Validation")
    st.dataframe(pd.DataFrame([quality]), width="stretch", hide_index=True)
    st.caption(
        "Transaction counts are an enrollment proxy only if each transaction "
        "represents one enrollment."
    )


# TAB 2: Instructor performance
with tabs[1]:
    st.subheader("Instructor Performance Leaderboard")

    possible_sort_columns = [
        column
        for column in [
            "TeacherRating",
            "MeanAssociatedCourseRating",
            "TransactionCount",
            "YearsOfExperience",
        ]
        if column in filtered_stats.columns
    ]

    if filtered_stats.empty:
        st.info("No instructor records match the selected filters.")
    elif not possible_sort_columns:
        st.warning("No supported ranking columns were found in the instructor summary.")
        st.dataframe(filtered_stats, width="stretch", hide_index=True)
    else:
        sort_column = st.selectbox(
            "Rank instructors by",
            options=possible_sort_columns,
            key="leaderboard_sort_column",
        )
        ascending = st.checkbox("Sort ascending", value=False)
        leaderboard = filtered_stats.sort_values(
            sort_column,
            ascending=ascending,
            na_position="last",
        )

        display_columns = [
            column
            for column in [
                "TeacherID",
                "TeacherName",
                "Expertise",
                "YearsOfExperience",
                "TeacherRating",
                "AssociatedCourseCount",
                "MeanAssociatedCourseRating",
                "CourseRatingSD",
                "TransactionCount",
            ]
            if column in leaderboard.columns
        ]

        st.dataframe(
            leaderboard[display_columns],
            width="stretch",
            hide_index=True,
        )
        st.download_button(
            "Download Leaderboard CSV",
            data=leaderboard[display_columns].to_csv(index=False).encode("utf-8"),
            file_name="edupro_instructor_leaderboard.csv",
            mime="text/csv",
        )


# TAB 3: Experience analysis
with tabs[2]:
    st.subheader("Experience and Performance")

    if filtered_teachers.empty:
        st.info("No instructors match the selected filters.")
    else:
        st.plotly_chart(
            experience_scatter(filtered_teachers),
            width="stretch",
            config={"displayModeBar": True, "responsive": True},
            key="tab2_experience_scatter",
        )

    correlation_rows = [
        {"Analysis": name, **result}
        for name, result in correlations.items()
    ]
    if correlation_rows:
        st.dataframe(
            pd.DataFrame(correlation_rows),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No correlation results are available.")

    st.caption(
        "Pearson measures linear association; Spearman measures monotonic "
        "association. Correlation does not establish causation."
    )


# TAB 4: Course quality
with tabs[3]:
    st.subheader("Course Quality by Category")

    if "CourseCategory" in category.columns:
        filtered_category = category[
            category["CourseCategory"].astype(str).isin(selected_categories)
        ]
    else:
        filtered_category = category.iloc[0:0].copy()

    if filtered_category.empty:
        st.info("No course categories match the selected filters.")
    else:
        st.plotly_chart(
            category_bar(filtered_category),
            width="stretch",
            config={"displayModeBar": True, "responsive": True},
            key="tab3_category_bar",
        )

    st.subheader("Course Quality by Level")
    if {"CourseLevel"}.issubset(level.columns):
        filtered_level = level[
            level["CourseLevel"].astype(str).isin(selected_levels)
        ]
    else:
        filtered_level = level.iloc[0:0].copy()

    st.dataframe(filtered_level, width="stretch", hide_index=True)

    if not filtered_courses.empty:
        filtered_pivot = filtered_courses.pivot_table(
            index="CourseCategory",
            columns="CourseLevel",
            values="CourseRating",
            aggfunc="mean",
        )
        if not filtered_pivot.empty:
            st.subheader("Average Course Rating Heatmap")
            st.plotly_chart(
                heatmap_figure(filtered_pivot),
                width="stretch",
                config={"displayModeBar": True, "responsive": True},
                key="tab3_heatmap",
            )
    else:
        st.info("No courses match the selected filters.")

    st.subheader("Filtered Courses")
    st.dataframe(filtered_courses, width="stretch", hide_index=True)


# TAB 5: Expertise analysis
with tabs[4]:
    st.subheader("Expertise-Wise Instructor Performance")

    if "Expertise" in expertise.columns:
        filtered_expertise = expertise[
            expertise["Expertise"].astype(str).isin(selected_expertise)
        ]
    else:
        filtered_expertise = expertise.iloc[0:0].copy()

    if filtered_expertise.empty:
        st.info("No expertise records match the selected filters.")
    else:
        st.plotly_chart(
            expertise_bar(filtered_expertise),
            width="stretch",
            config={"displayModeBar": True, "responsive": True},
            key="tab4_expertise_bar",
        )
        st.dataframe(filtered_expertise, width="stretch", hide_index=True)


# TAB 6: Enrollment and data quality
with tabs[5]:
    st.subheader("Instructor Rating vs Transaction Volume")

    required_scatter_columns = {
        "TeacherRating",
        "TransactionCount",
        "Expertise",
        "TeacherName",
    }
    if (
        not filtered_stats.empty
        and required_scatter_columns.issubset(filtered_stats.columns)
    ):
        figure = px.scatter(
            filtered_stats,
            x="TeacherRating",
            y="TransactionCount",
            color="Expertise",
            hover_name="TeacherName",
            title="Teacher Rating vs Transaction Count",
        )
        st.plotly_chart(
            figure,
            width="stretch",
            config={"displayModeBar": True, "responsive": True},
            key="tab6_rating_vs_transaction_scatter",
        )

        tiered = add_rating_tiers(filtered_stats)
        if "RatingTier" in tiered.columns:
            tier_summary = (
                tiered.groupby("RatingTier", dropna=False)
                .agg(
                    InstructorCount=("TeacherID", "nunique"),
                    MeanTeacherRating=("TeacherRating", "mean"),
                    MeanTransactionCount=("TransactionCount", "mean"),
                    MedianTransactionCount=("TransactionCount", "median"),
                )
                .reset_index()
            )
            st.subheader("Instructor Rating Tier Comparison")
            st.dataframe(tier_summary, width="stretch", hide_index=True)
        else:
            st.info("Rating-tier labels were not produced by add_rating_tiers().")
    else:
        st.info("Not enough instructor summary data is available for this chart.")

    if "Amount" in transactions.columns:
        amounts = pd.to_numeric(transactions["Amount"], errors="coerce")
        valid_amounts = amounts.dropna()
        st.subheader("Transaction Amount Analysis")
        amount_columns = st.columns(3)
        zero_share = (amounts == 0).mean() if not amounts.empty else float("nan")
        amount_columns[0].metric("Zero-Amount Share", f"{zero_share:.1%}")
        amount_columns[1].metric(
            "Mean Amount",
            f"{valid_amounts.mean():.2f}" if not valid_amounts.empty else "N/A",
        )
        amount_columns[2].metric(
            "Median Amount",
            f"{valid_amounts.median():.2f}" if not valid_amounts.empty else "N/A",
        )
    else:
        st.info("No Amount column exists in the transactions data.")

    st.subheader("Join Validation")
    st.dataframe(pd.DataFrame([quality]), width="stretch", hide_index=True)
    st.caption(
        "A course linked to multiple TeacherIDs does not establish exclusive "
        "instructor ownership of that course."
    )
