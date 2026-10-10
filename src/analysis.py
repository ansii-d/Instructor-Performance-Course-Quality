
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


def correlation_result(x, y, method="pearson"):
    data = pd.DataFrame({
        "x": x,
        "y": y,
    }).replace([np.inf, -np.inf], np.nan).dropna()

    if (
        len(data) < 3
        or data["x"].nunique() < 2
        or data["y"].nunique() < 2
    ):
        return {
            "n": len(data),
            "coefficient": np.nan,
            "p_value": np.nan,
        }

    if method == "pearson":
        result = pearsonr(data["x"], data["y"])
    else:
        result = spearmanr(data["x"], data["y"])

    return {
        "n": len(data),
        "coefficient": float(result.statistic),
        "p_value": float(result.pvalue),
    }


def instructor_summary(teachers, courses, transactions):
    # Count unique transactions associated with each teacher.
    transaction_counts = (
        transactions.groupby("TeacherID")["TransactionID"]
        .nunique()
        .rename("TransactionCount")
    )

    # Use distinct teacher-course pairs so transactions do not
    # repeatedly weight the same course rating.
    associations = transactions[
        ["TeacherID", "CourseID"]
    ].drop_duplicates()

    associated_courses = associations.merge(
        courses[["CourseID", "CourseRating"]],
        on="CourseID",
        how="left",
        validate="many_to_one",
    )

    course_stats = associated_courses.groupby("TeacherID").agg(
        AssociatedCourseCount=("CourseID", "nunique"),
        MeanAssociatedCourseRating=("CourseRating", "mean"),
        CourseRatingSD=("CourseRating", "std"),
    )

    result = teachers.merge(
        transaction_counts,
        on="TeacherID",
        how="left",
    ).merge(
        course_stats,
        on="TeacherID",
        how="left",
    )

    result["TransactionCount"] = (
        result["TransactionCount"].fillna(0).astype(int)
    )

    return result


def experience_correlations(teachers, instructor_stats):
    return {
        "Experience vs Teacher Rating (Pearson)": (
            correlation_result(
                teachers["YearsOfExperience"],
                teachers["TeacherRating"],
            )
        ),
        "Experience vs Teacher Rating (Spearman)": (
            correlation_result(
                teachers["YearsOfExperience"],
                teachers["TeacherRating"],
                "spearman",
            )
        ),
        "Experience vs Associated Course Rating (Pearson)": (
            correlation_result(
                instructor_stats["YearsOfExperience"],
                instructor_stats["MeanAssociatedCourseRating"],
            )
        ),
        "Teacher Rating vs Transaction Count (Pearson)": (
            correlation_result(
                instructor_stats["TeacherRating"],
                instructor_stats["TransactionCount"],
            )
        ),
        "Teacher Rating vs Transaction Count (Spearman)": (
            correlation_result(
                instructor_stats["TeacherRating"],
                instructor_stats["TransactionCount"],
                "spearman",
            )
        ),
    }


def add_rating_tiers(instructor_stats):
    result = instructor_stats.copy()
    ratings = result["TeacherRating"].dropna()

    if ratings.nunique() < 3:
        result["RatingTier"] = "Insufficient variation"
        return result

    lower, upper = ratings.quantile([1 / 3, 2 / 3])

    result["RatingTier"] = np.select(
        [
            result["TeacherRating"] <= lower,
            result["TeacherRating"] <= upper,
        ],
        ["Low", "Mid"],
        default="High",
    )

    return result


def expertise_summary(teachers):
    return (
        teachers.groupby("Expertise", dropna=False)
        .agg(
            InstructorCount=("TeacherID", "nunique"),
            AverageTeacherRating=("TeacherRating", "mean"),
            MedianTeacherRating=("TeacherRating", "median"),
            AverageExperience=("YearsOfExperience", "mean"),
            RatingSD=("TeacherRating", "std"),
        )
        .reset_index()
        .sort_values("AverageTeacherRating", ascending=False)
    )


def course_quality_summary(courses):
    category = (
        courses.groupby("CourseCategory", dropna=False)
        .agg(
            CourseCount=("CourseID", "nunique"),
            AverageCourseRating=("CourseRating", "mean"),
            MedianCourseRating=("CourseRating", "median"),
            RatingSD=("CourseRating", "std"),
        )
        .reset_index()
        .sort_values("AverageCourseRating", ascending=False)
    )

    level = (
        courses.groupby("CourseLevel", dropna=False)
        .agg(
            CourseCount=("CourseID", "nunique"),
            AverageCourseRating=("CourseRating", "mean"),
            MedianCourseRating=("CourseRating", "median"),
            RatingSD=("CourseRating", "std"),
        )
        .reset_index()
        .sort_values("AverageCourseRating", ascending=False)
    )

    heatmap = courses.pivot_table(
        index="CourseCategory",
        columns="CourseLevel",
        values="CourseRating",
        aggfunc="mean",
    )

    return category, level, heatmap
