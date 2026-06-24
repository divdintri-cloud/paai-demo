import json
import os
from pathlib import Path


def get_context_path():
    data_dir = Path(os.getenv("PAAI_DATA_DIR", "data"))
    return data_dir / "user_context.json"


DEFAULT_CONTEXT = {
    "current_priorities": [
        "Use PAAI safely",
        "Explore available agents",
        "Give useful feedback"
    ],
    "active_projects": [
        "PAAI"
    ],
    "short_term_goals": [
        "Test PAAI",
        "Review agent behavior",
        "Collect feedback"
    ],
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
}


def load_user_context():
    context_path = get_context_path()

    if not context_path.exists():
        context_path.parent.mkdir(parents=True, exist_ok=True)
        save_user_context(DEFAULT_CONTEXT)
        return DEFAULT_CONTEXT

    try:
        context = json.loads(context_path.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_CONTEXT

    merged_context = DEFAULT_CONTEXT.copy()
    merged_context.update(context)
    return merged_context


def save_user_context(context):
    context_path = get_context_path()
    context_path.parent.mkdir(parents=True, exist_ok=True)
    context_path.write_text(json.dumps(context, indent=2), encoding="utf-8")
    return context
