
from pathlib import Path
def require_columns(df, columns, label):
    missing = sorted(set(columns) - set(df.columns))

    if missing:
        raise ValueError(
            f"{label} is missing required columns: {missing}"
        )


def clean_teachers(df):
    df = df.copy()

    require_columns(
        df,
        [
            "TeacherID",
            "TeacherName",
            "TeacherRating",
            "YearsOfExperience",
            "Expertise",
        ],
        "Teachers.csv",
    )

    for column in [
        "TeacherRating",
        "YearsOfExperience",
        "Age",
    ]:
        if column in df.columns:
            df[column] = __import__("pandas").to_numeric(
                df[column], errors="coerce"
            )

    return df.drop_duplicates(
        subset=["TeacherID"], keep="first"
    )


def clean_courses(df):
    df = df.copy()

    require_columns(
        df,
        [
            "CourseID",
            "CourseName",
            "CourseCategory",
            "CourseLevel",
            "CourseRating",
        ],
        "Courses.csv",
    )

    import pandas as pd

    df["CourseRating"] = pd.to_numeric(
        df["CourseRating"], errors="coerce"
    )

    return df.drop_duplicates(
        subset=["CourseID"], keep="first"
    )


def clean_transactions(df):
    df = df.copy()

    require_columns(
        df,
        ["TransactionID", "TeacherID", "CourseID"],
        "Transactions.csv",
    )

    return df.drop_duplicates(
        subset=["TransactionID"], keep="first"
    )


def create_master_dataset(
    teachers, courses, transactions
):
    # Each ID must identify one record in its dimension table.
    if teachers["TeacherID"].duplicated().any():
        raise ValueError("TeacherID must be unique.")

    if courses["CourseID"].duplicated().any():
        raise ValueError("CourseID must be unique.")

    if transactions["TransactionID"].duplicated().any():
        raise ValueError("TransactionID must be unique.")

    master = transactions.merge(
        teachers,
        on="TeacherID",
        how="left",
        validate="many_to_one",
        indicator="_teacher_match",
    )

    master = master.merge(
        courses,
        on="CourseID",
        how="left",
        validate="many_to_one",
        indicator="_course_match",
        suffixes=("_teacher", "_course"),
    )

    return master


def data_quality_report(
    teachers, courses, transactions, master
):
    return {
        "Teacher rows": len(teachers),
        "Course rows": len(courses),
        "Transaction rows": len(transactions),
        "Unmatched teacher records": int(
            (master["_teacher_match"] == "left_only").sum()
        ),
        "Unmatched course records": int(
            (master["_course_match"] == "left_only").sum()
        ),
        "Joined rows": len(master),
    }
 



def save_processed_data(
    teachers,
    courses,
    transactions,
    master,
):
    """Save cleaned datasets and the joined master dataset."""

    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"

    processed_dir.mkdir(parents=True, exist_ok=True)

    teachers.to_csv(
        processed_dir / "teachers_cleaned.csv",
        index=False,
    )

    courses.to_csv(
        processed_dir / "courses_cleaned.csv",
        index=False,
    )

    transactions.to_csv(
        processed_dir / "transactions_cleaned.csv",
        index=False,
    )

    master.to_csv(
        processed_dir / "master_dataset.csv",
        index=False,
    )

    return processed_dir
