from pathlib import Path

import pandas as pd

DATA_DIR = Path("data")


def read_text_file(file_name):
    path = DATA_DIR / file_name

    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8")


def read_csv_file(file_name):
    path = DATA_DIR / file_name

    if not path.exists():
        return ""

    df = pd.read_csv(path)
    return df.to_string(index=False)


def load_all_context():
    return {
        "personal_profile": read_text_file("personal_profile.md"),
        "grocery_profile": read_text_file("grocery_profile.md"),
        "entertainment_preferences": read_text_file("entertainment_preferences.md"),
        "reading_preferences": read_text_file("reading_preferences.md"),
        "books_inventory": read_csv_file("books_inventory.csv"),
        "ai_pm_transition_plan": read_text_file("ai_pm_transition_plan.md"),
        "ai_project_portfolio": read_text_file("ai_project_portfolio.md"),
        "payment_reminders": read_csv_file("payment_reminders.csv"),
        "travel_preferences": read_text_file("travel_preferences.md"),
        "tasks": read_csv_file("tasks.csv"),
    }
