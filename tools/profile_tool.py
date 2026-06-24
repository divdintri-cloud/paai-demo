import json
import os
from pathlib import Path


def get_profile_path():
    data_dir = Path(os.getenv("PAAI_DATA_DIR", "data"))
    return data_dir / "user_profile.json"


DEFAULT_PROFILE = {
    "name": "User",
    "timezone": "America/Chicago",
    "primary_goal": "",
    "preferred_style": "Clear, practical, beginner-friendly",
    "privacy_preference": "Keep personal data local",
    "current_project": "PAAI 1.0",
    "career_focus": "",
    "learning_focus": "",
    "response_preference": "",
    "notes": "",
}


def load_user_profile():
    profile_path = get_profile_path()

    if not profile_path.exists():
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        save_user_profile(DEFAULT_PROFILE)
        return DEFAULT_PROFILE

    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_PROFILE

    merged_profile = DEFAULT_PROFILE.copy()
    merged_profile.update(profile)
    return merged_profile


def save_user_profile(profile):
    profile_path = get_profile_path()
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return profile
