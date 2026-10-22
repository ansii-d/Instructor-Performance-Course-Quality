from pathlib import Path
import numpy as np
import pandas as pd


def load_raw_data(raw_dir: Path):
    """Load raw CSV datasets or generate synthetic mock data if files are missing."""
    teachers_path = raw_dir / "Teachers.csv"
    courses_path = raw_dir / "Courses.csv"
    transactions_path = raw_dir / "Transactions.csv"

    if (
        not teachers_path.exists()
        or not courses_path.exists()
        or not transactions_path.exists()
    ):
        teachers_df = pd.DataFrame(
            {
                "TeacherID": [f"T{i:03d}" for i in range(1, 31)],
                "TeacherName": [f"Instructor {i}" for i in range(1, 31)],
                "Age": np.random.randint(28, 55, 30),
                "Gender": np.random.choice(["Male", "Female"], 30),
                "Expertise": np.random.choice(
                    [
                        "Data Science",
                        "Web Development",
                        "AI & ML",
                        "Business",
                        "Design",
                    ],
                    30,
                ),
                "YearsOfExperience": np.random.randint(1, 15, 30),
                "TeacherRating": np.random.uniform(3.5, 5.0, 30).round(2),
            }
        )
        courses_df = pd.DataFrame(
            {
                "CourseID": [f"C{i:03d}" for i in range(1, 51)],
                "CourseName": [f"Course {i}" for i in range(1, 51)],
                "CourseCategory": np.random.choice(
                    [
                        "Data Science",
                        "Web Development",
                        "AI & ML",
                        "Business",
                        "Design",
                    ],
                    50,
                ),
                "CourseLevel": np.random.choice(
                    ["Beginner", "Intermediate", "Advanced"], 50
                ),
                "CourseRating": np.random.uniform(3.0, 5.0, 50).round(2),
            }
        )
        transactions_df = pd.DataFrame(
            {
                "TransactionID": [f"TXN{i:05d}" for i in range(1, 201)],
                "TeacherID": np.random.choice(teachers_df["TeacherID"], 200),
                "CourseID": np.random.choice(courses_df["CourseID"], 200),
            }
        )
        return teachers_df, courses_df, transactions_df

    return (
        pd.read_csv(teachers_path),
        pd.read_csv(courses_path),
        pd.read_csv(transactions_path),
    )