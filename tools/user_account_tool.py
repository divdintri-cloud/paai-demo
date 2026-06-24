import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


USERS_ROOT = Path("data") / "users"


def slugify_user_id(display_name):
    base = str(display_name or "user").strip().lower()
    base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")
    return base or "user"


def normalize_tester_code(tester_code):
    return str(tester_code or "").strip()


def hash_tester_code(tester_code):
    normalized_code = normalize_tester_code(tester_code)

    if not normalized_code:
        return ""

    return hashlib.sha256(normalized_code.encode("utf-8")).hexdigest()


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

    return sorted(users, key=lambda item: item.get("display_name", "").lower())


def find_account_by_tester_code(tester_code):
    code_hash = hash_tester_code(tester_code)

    if not code_hash:
        return None

    for account in list_users():
        if account.get("tester_code_hash") == code_hash:
            return account

    return None


def register_user(
    display_name,
    tester_code,
    optional_email="",
    consent_to_save_feedback=False,
    consent_to_use_feedback_for_training=False,
):
    display_name = str(display_name or "").strip()
    tester_code = normalize_tester_code(tester_code)

    if not display_name:
        raise ValueError("Display name is required.")

    if len(tester_code) < 4:
        raise ValueError("Tester code must be at least 4 characters.")

    user_id = slugify_user_id(display_name)
    existing_code_owner = find_account_by_tester_code(tester_code)

    if existing_code_owner and existing_code_owner.get("user_id") != user_id:
        raise ValueError("That tester code is already in use. Choose a different code.")

    user_dir = get_user_data_dir(user_id)

    account = {
        "user_id": user_id,
        "display_name": display_name,
        "optional_email": str(optional_email or "").strip(),
        "tester_code_hash": hash_tester_code(tester_code),
        "consent_to_save_feedback": bool(consent_to_save_feedback),
        "consent_to_use_feedback_for_training": bool(consent_to_use_feedback_for_training),
        "created_or_updated_at": datetime.now().isoformat(timespec="seconds"),
        "data_dir": str(user_dir),
    }

    get_user_account_path(user_id).write_text(
        json.dumps(account, indent=2),
        encoding="utf-8",
    )

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


def authenticate_user_by_code(tester_code):
    return find_account_by_tester_code(tester_code)


# Backward-compatible wrapper for older app code.
def create_or_update_user(
    display_name,
    optional_email="",
    consent_to_save_feedback=False,
    consent_to_use_feedback_for_training=False,
):
    fallback_code = slugify_user_id(display_name) + "_local"
    return register_user(
        display_name=display_name,
        tester_code=fallback_code,
        optional_email=optional_email,
        consent_to_save_feedback=consent_to_save_feedback,
        consent_to_use_feedback_for_training=consent_to_use_feedback_for_training,
    )
