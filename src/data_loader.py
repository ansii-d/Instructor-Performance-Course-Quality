
from pathlib import Path
import pandas as pd

# Project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"


def read_csv(filename):
    """Load a CSV file from the raw data folder."""
    file_path = RAW_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}\n"
            "Place the required CSV file inside data/raw/."
        )

    return pd.read_csv(file_path)


def load_teachers():
    return read_csv("Teachers.csv")


def load_courses():
    return read_csv("Courses.csv")


def load_transactions():
    return read_csv("Transactions.csv")


def load_users():
    """Users data is optional for this project."""
    file_path = RAW_DIR / "Users.csv"

    if file_path.exists():
        return pd.read_csv(file_path)

    return None


def load_all_data():
    teachers = load_teachers()
    courses = load_courses()
    transactions = load_transactions()

    return teachers, courses, transactions
