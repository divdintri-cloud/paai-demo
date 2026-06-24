import json
import re
from datetime import datetime
from pathlib import Path


USERS_ROOT = Path("data") / "users"


def slugify_user_id(display_name):
    base = str(display_name or "user").strip().lower()
    base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")
    return base or "user"


def get_user_data_dir(user_id):
    safe_user_id = slugify_user_id(user_id)
    user_dir = USERS_ROOT / safe_user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_account_path(user_id):
    return get_user_data_dir(user_id) / "user_account.json"


def list_users():
    USERS_ROOT.mkdir(parents=True, exist_ok=True)

    users = []

    for account_file in USERS_ROOT.glob("*/user_account.json"):
        try:
            account = json.loads(account_file.read_text(encoding="utf-8"))
            users.append(account)
        except Exception:
            continue

    users = sorted(users, key=lambda item: item.get("display_name", "").lower())
    return users


def create_or_update_user(
    display_name,
    optional_email="",
    consent_to_save_feedback=False,
    consent_to_use_feedback_for_training=False,
):
    display_name = str(display_name or "").strip()

    if not display_name:
        raise ValueError("Display name is required.")

    user_id = slugify_user_id(display_name)
    user_dir = get_user_data_dir(user_id)

    account = {
        "user_id": user_id,
        "display_name": display_name,
        "optional_email": optional_email,
        "consent_to_save_feedback": bool(consent_to_save_feedback),
        "consent_to_use_feedback_for_training": bool(consent_to_use_feedback_for_training),
        "created_or_updated_at": datetime.now().isoformat(timespec="seconds"),
        "data_dir": str(user_dir),
    }

    get_user_account_path(user_id).write_text(
        json.dumps(account, indent=2),
        encoding="utf-8",
    )

    # Create starter profile if missing.
    profile_path = user_dir / "user_profile.json"
    if not profile_path.exists():
        profile_path.write_text(
            json.dumps(
                {
                    "name": display_name,
                    "timezone": "America/Chicago",
                    "primary_goal": "",
                    "preferred_style": "Clear, practical, beginner-friendly",
                    "privacy_preference": "Keep personal data local",
                    "current_project": "PAAI",
                    "career_focus": "",
                    "learning_focus": "",
                    "response_preference": "",
                    "notes": "",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    # Create starter context if missing.
    context_path = user_dir / "user_context.json"
    if not context_path.exists():
        context_path.write_text(
            json.dumps(
                {
                    "current_priorities": [],
                    "active_projects": ["PAAI"],
                    "short_term_goals": [],
                    "long_term_goals": [],
                    "assistant_should": [
                        "Be clear",
                        "Be helpful",
                        "Protect privacy"
                    ],
                    "assistant_should_not": [
                        "Expose personal details in Demo mode"
                    ],
                    "privacy_notes": [
                        "Personal data should stay local"
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    return account
