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


def get_account_by_user_id(user_id):
    account_path = get_user_account_path(user_id)

    if not account_path.exists():
        return None

    try:
        return json.loads(account_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def register_user(
    display_name,
    tester_code,
    optional_email="",
    consent_to_save_feedback=False,
    consent_to_use_feedback_for_training=False,
    primary_goal="",
    role_or_stage="",
    learning_focus="",
    interests="",
    preferred_response_style="",
    literacy_goal="",
    privacy_notes="",
    **extra_context,
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
        "primary_goal": str(primary_goal or "").strip(),
        "role_or_stage": str(role_or_stage or "").strip(),
        "learning_focus": str(learning_focus or "").strip(),
        "interests": str(interests or "").strip(),
        "preferred_response_style": str(preferred_response_style or "").strip(),
        "literacy_goal": str(literacy_goal or "").strip(),
        "privacy_notes": str(privacy_notes or "").strip(),
        "extra_context": extra_context,
        "created_or_updated_at": datetime.now().isoformat(timespec="seconds"),
        "data_dir": str(user_dir),
    }

    get_user_account_path(user_id).write_text(
        json.dumps(account, indent=2),
        encoding="utf-8",
    )

    profile_path = user_dir / "user_profile.json"
    profile = {
        "name": display_name,
        "timezone": "America/Chicago",
        "primary_goal": account["primary_goal"],
        "preferred_style": account["preferred_response_style"] or "Clear, practical, beginner-friendly",
        "privacy_preference": account["privacy_notes"] or "Keep personal data local",
        "current_project": "PAAI",
        "career_focus": account["role_or_stage"],
        "learning_focus": account["learning_focus"],
        "response_preference": account["preferred_response_style"],
        "literacy_goal": account["literacy_goal"],
        "interests": account["interests"],
        "notes": "",
    }

    if profile_path.exists():
        try:
            existing_profile = json.loads(profile_path.read_text(encoding="utf-8"))
            existing_profile.update({key: value for key, value in profile.items() if value})
            profile = existing_profile
        except Exception:
            pass

    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    context_path = user_dir / "user_context.json"
    context = {
        "current_priorities": [account["primary_goal"]] if account["primary_goal"] else [],
        "active_projects": ["PAAI"],
        "short_term_goals": [account["learning_focus"]] if account["learning_focus"] else [],
        "long_term_goals": [],
        "assistant_should": [
            account["preferred_response_style"] or "Be clear",
            "Be helpful",
            "Protect privacy",
        ],
        "assistant_should_not": [
            "Expose personal details in Demo mode",
        ],
        "privacy_notes": [
            account["privacy_notes"] or "Personal data should stay local",
        ],
        "role_or_stage": account["role_or_stage"],
        "interests": account["interests"],
        "literacy_goal": account["literacy_goal"],
    }

    if context_path.exists():
        try:
            existing_context = json.loads(context_path.read_text(encoding="utf-8"))
            existing_context.update({key: value for key, value in context.items() if value})
            context = existing_context
        except Exception:
            pass

    context_path.write_text(json.dumps(context, indent=2), encoding="utf-8")

    return account


def authenticate_user_by_code(tester_code):
    return find_account_by_tester_code(tester_code)


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
