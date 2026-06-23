from datetime import datetime
import os
from pathlib import Path

import pandas as pd


def get_activity_log_path():
    return Path(os.getenv("PAAI_DATA_DIR", "data")) / "paai_activity_log.csv"


def log_activity(user_question, routed_agent, action, result_summary):
    get_activity_log_path().parent.mkdir(exist_ok=True)

    row = {
        "Timestamp": datetime.now().isoformat(timespec="seconds"),
        "User Question": user_question,
        "Routed Agent": routed_agent,
        "Action": action,
        "Result Summary": result_summary,
    }

    if get_activity_log_path().exists():
        df = pd.read_csv(get_activity_log_path())
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(get_activity_log_path(), index=False)

    return row


def load_activity_log():
    if not get_activity_log_path().exists():
        return pd.DataFrame(
            columns=[
                "Timestamp",
                "User Question",
                "Routed Agent",
                "Action",
                "Result Summary",
            ]
        )

    return pd.read_csv(get_activity_log_path())


def get_recent_activity(limit=10):
    df = load_activity_log()

    if df.empty:
        return df

    return df.tail(limit).sort_values("Timestamp", ascending=False)
