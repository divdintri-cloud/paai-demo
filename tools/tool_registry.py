from tools.profile_tool import load_user_profile, save_user_profile
from tools.context_tool import load_user_context, save_user_context
from tools.feedback_tool import save_feedback
from tools.training_export_tool import export_training_examples


def list_tools():
    return [
        {
            "name": "load_user_profile",
            "description": "Load the local user profile for Personal mode.",
            "status": "Available",
            "safe_in_demo": "No",
            "connects_to": "data/user_profile.json",
            "output_type": "JSON profile",
        },
        {
            "name": "save_user_profile",
            "description": "Save the local user profile for Personal mode.",
            "status": "Available",
            "safe_in_demo": "No",
            "connects_to": "data/user_profile.json",
            "output_type": "JSON profile",
        },
        {
            "name": "load_user_context",
            "description": "Load local manual user context for personalization.",
            "status": "Available",
            "safe_in_demo": "No",
            "connects_to": "data/user_context.json",
            "output_type": "JSON context",
        },
        {
            "name": "save_user_context",
            "description": "Save local manual user context.",
            "status": "Available",
            "safe_in_demo": "No",
            "connects_to": "data/user_context.json",
            "output_type": "JSON context",
        },
        {
            "name": "save_feedback",
            "description": "Save thumbs up/down feedback for evals and training readiness.",
            "status": "Available",
            "safe_in_demo": "Yes",
            "connects_to": "evals/paai_feedback_log.csv",
            "output_type": "CSV row",
        },
        {
            "name": "export_training_examples",
            "description": "Export feedback marked for training into CSV and JSONL files.",
            "status": "Available",
            "safe_in_demo": "No",
            "connects_to": "evals/paai_feedback_log.csv",
            "output_type": "CSV + JSONL",
        },
    ]


def call_tool(tool_name, arguments=None):
    arguments = arguments or {}

    if tool_name == "load_user_profile":
        return load_user_profile()

    if tool_name == "save_user_profile":
        return save_user_profile(arguments.get("profile", {}))

    if tool_name == "load_user_context":
        return load_user_context()

    if tool_name == "save_user_context":
        return save_user_context(arguments.get("context", {}))

    if tool_name == "save_feedback":
        return save_feedback(**arguments)

    if tool_name == "export_training_examples":
        return export_training_examples()

    raise ValueError(f"Unknown tool: {tool_name}")
