
import numpy as np
import pandas as pd


def calculate_kpis(
    teachers, courses, transactions, instructor_stats
):
    rating_sd = (
        instructor_stats["CourseRatingSD"].dropna()
    )

    # Higher values indicate lower observed rating variation.
    consistency_index = (
        1 / (1 + rating_sd.mean())
        if len(rating_sd) > 0
        else np.nan
    )

    # This is association, not a causal influence measure.
    correlation_data = instructor_stats[
        ["TeacherRating", "TransactionCount"]
    ].dropna()

    if (
        len(correlation_data) >= 3
        and correlation_data.nunique().min() > 1
    ):
        enrollment_correlation = (
            correlation_data.corr().iloc[0, 1]
        )
    else:
        enrollment_correlation = np.nan

    kpis = {
        "Instructor count": int(
            teachers["TeacherID"].nunique()
        ),
        "Course count": int(
            courses["CourseID"].nunique()
        ),
        "Transaction count": int(
            transactions["TransactionID"].nunique()
        ),
        "Average teacher rating": float(
            teachers["TeacherRating"].mean()
        ),
        "Average course rating": float(
            courses["CourseRating"].mean()
        ),
        "Average experience (years)": float(
            teachers["YearsOfExperience"].mean()
        ),
        "Rating consistency index": float(
            consistency_index
        ),
        "Teacher rating / transaction correlation": float(
            enrollment_correlation
        ),
    }

    if "Amount" in transactions.columns:
        amount = pd.to_numeric(
            transactions["Amount"], errors="coerce"
        )

        kpis["Zero-amount transaction share"] = float(
            (amount == 0).mean()
        )
        kpis["Mean transaction amount"] = float(
            amount.mean()
        )
        kpis["Median transaction amount"] = float(
            amount.median()
        )

    return kpis
