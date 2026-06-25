import csv
import json
from pathlib import Path

import pandas as pd


FEEDBACK_PATH = Path("evals") / "paai_feedback_log.csv"
TRAINING_CSV_PATH = Path("evals") / "training_examples_export.csv"
TRAINING_JSONL_PATH = Path("evals") / "training_examples_export.jsonl"


REQUIRED_COLUMNS = [
    "Timestamp",
    "Mode",
    "Agent",
    "Tester Name",
    "User Question",
    "Helpful",
    "Correction Notes",
    "Ideal Answer",
    "Agent Response Summary",
    "Use For Training",
]


def load_feedback_log():
    if not FEEDBACK_PATH.exists():
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    try:
        df = pd.read_csv(FEEDBACK_PATH, engine="python", on_bad_lines="skip")
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    return df[REQUIRED_COLUMNS]


def get_training_ready_feedback():
    df = load_feedback_log()

    if df.empty:
        return df

    training_df = df[
        df["Use For Training"].astype(str).str.lower().str.strip() == "yes"
    ].copy()

    training_df = training_df[
        training_df["User Question"].astype(str).str.strip().ne("")
    ]

    training_df = training_df[
        training_df["Ideal Answer"].astype(str).str.strip().ne("")
    ]

    return training_df


def export_training_examples():
    training_df = get_training_ready_feedback()

    TRAINING_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    export_columns = [
        "Agent",
        "User Question",
        "Ideal Answer",
        "Correction Notes",
        "Agent Response Summary",
        "Helpful",
        "Mode",
        "Timestamp",
    ]

    if training_df.empty:
        empty_df = pd.DataFrame(columns=export_columns)
        empty_df.to_csv(TRAINING_CSV_PATH, index=False)
        TRAINING_JSONL_PATH.write_text("", encoding="utf-8")

        return {
            "exported_count": 0,
            "csv_path": str(TRAINING_CSV_PATH),
            "jsonl_path": str(TRAINING_JSONL_PATH),
        }

    clean_df = training_df[export_columns].copy()
    clean_df.to_csv(TRAINING_CSV_PATH, index=False)

    with TRAINING_JSONL_PATH.open("w", encoding="utf-8") as f:
        for _, row in clean_df.iterrows():
            record = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are PAAI, a helpful personal AI assistant. "
                            "Answer according to the selected agent and user context. "
                            "Protect private information and avoid exposing sensitive data."
                        ),
                    },
                    {
                        "role": "user",
                        "content": str(row["User Question"]),
                    },
                    {
                        "role": "assistant",
                        "content": str(row["Ideal Answer"]),
                    },
                ],
                "metadata": {
                    "agent": str(row["Agent"]),
                    "mode": str(row["Mode"]),
                    "helpful": str(row["Helpful"]),
                    "correction_notes": str(row["Correction Notes"]),
                    "agent_response_summary": str(row["Agent Response Summary"]),
                    "timestamp": str(row["Timestamp"]),
                },
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "exported_count": len(clean_df),
        "csv_path": str(TRAINING_CSV_PATH),
        "jsonl_path": str(TRAINING_JSONL_PATH),
    }
