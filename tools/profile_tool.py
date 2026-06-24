import json
from pathlib import Path


PROFILE_PATH = Path("data") / "user_profile.json"


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
    if not PROFILE_PATH.exists():
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        save_user_profile(DEFAULT_PROFILE)
        return DEFAULT_PROFILE

    try:
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_PROFILE

    merged_profile = DEFAULT_PROFILE.copy()
    merged_profile.update(profile)
    return merged_profile


def save_user_profile(profile):
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return profile
