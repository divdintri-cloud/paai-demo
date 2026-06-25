from datetime import datetime
from pathlib import Path

import pandas as pd


GLOBAL_FEEDBACK_LOG_PATH = Path("evals") / "paai_feedback_log.csv"


FEEDBACK_COLUMNS = [
    "Timestamp",
    "Mode",
    "Agent",
    "Active User ID",
    "Active User Name",
    "Tester Name",
    "User Question",
    "Helpful",
    "Correction Notes",
    "Ideal Answer",
    "Agent Response Summary",
    "Use For Training",
    "Consent To Save Feedback",
    "Consent To Use Feedback For Training",
    "Saved To User Log",
]


def _append_feedback_row(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        try:
            feedback_df = pd.read_csv(path, engine="python", on_bad_lines="skip")
        except Exception:
            feedback_df = pd.DataFrame(columns=FEEDBACK_COLUMNS)
    else:
        feedback_df = pd.DataFrame(columns=FEEDBACK_COLUMNS)

    for column in FEEDBACK_COLUMNS:
        if column not in feedback_df.columns:
            feedback_df[column] = ""

    feedback_df = pd.concat([feedback_df, pd.DataFrame([row])], ignore_index=True)
    feedback_df = feedback_df[FEEDBACK_COLUMNS]
    feedback_df.to_csv(path, index=False)


def _get_user_feedback_path(active_user_id):
    safe_user_id = str(active_user_id or "").strip()

    if not safe_user_id or safe_user_id == "demo":
        return None

    return Path("data") / "users" / safe_user_id / "feedback_log.csv"


def save_feedback(
    mode,
    agent,
    tester_name,
    user_question,
    helpful,
    correction_notes,
    ideal_answer,
    agent_response_summary,
    use_for_training,
    active_user_id="",
    active_user_name="",
    consent_to_save_feedback=True,
    consent_to_use_feedback_for_training=False,
):
    mode = str(mode or "Demo")
    active_user_id = str(active_user_id or "").strip()
    active_user_name = str(active_user_name or "").strip()

    # Respect consent in Personal mode.
    if mode == "Personal" and not consent_to_save_feedback:
        return {
            "saved": False,
            "reason": "User did not consent to save feedback.",
            "active_user_id": active_user_id,
            "active_user_name": active_user_name,
        }

    # Do not allow training use unless user consented.
    safe_use_for_training = use_for_training
    if not consent_to_use_feedback_for_training:
        safe_use_for_training = "No"

    row = {
        "Timestamp": datetime.now().isoformat(timespec="seconds"),
        "Mode": mode,
        "Agent": agent,
        "Active User ID": active_user_id,
        "Active User Name": active_user_name,
        "Tester Name": tester_name,
        "User Question": user_question,
        "Helpful": helpful,
        "Correction Notes": correction_notes,
        "Ideal Answer": ideal_answer,
        "Agent Response Summary": agent_response_summary,
        "Use For Training": safe_use_for_training,
        "Consent To Save Feedback": bool(consent_to_save_feedback),
        "Consent To Use Feedback For Training": bool(consent_to_use_feedback_for_training),
        "Saved To User Log": False,
    }

    user_feedback_path = _get_user_feedback_path(active_user_id)

    if user_feedback_path is not None:
        user_row = row.copy()
        user_row["Saved To User Log"] = True
        _append_feedback_row(user_feedback_path, user_row)
        row["Saved To User Log"] = True

    _append_feedback_row(GLOBAL_FEEDBACK_LOG_PATH, row)

    return {
        "saved": True,
        "global_feedback_log": str(GLOBAL_FEEDBACK_LOG_PATH),
        "user_feedback_log": str(user_feedback_path) if user_feedback_path else "",
        "row": row,
    }
