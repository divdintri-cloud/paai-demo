import csv
from datetime import datetime
from pathlib import Path


FEEDBACK_PATH = Path("evals") / "paai_feedback_log.csv"

FEEDBACK_COLUMNS = [
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


def ensure_feedback_log():
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not FEEDBACK_PATH.exists() or FEEDBACK_PATH.stat().st_size == 0:
        with FEEDBACK_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(FEEDBACK_COLUMNS)


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
):
    ensure_feedback_log()

    with FEEDBACK_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            mode,
            agent,
            tester_name,
            user_question,
            helpful,
            correction_notes,
            ideal_answer,
            agent_response_summary,
            use_for_training,
        ])

    return {
        "saved": True,
        "path": str(FEEDBACK_PATH),
        "helpful": helpful,
        "use_for_training": use_for_training,
    }
