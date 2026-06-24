from tools.profile_tool import load_user_profile, save_user_profile
from tools.context_tool import load_user_context, save_user_context
from tools.feedback_tool import save_feedback


def list_tools():
    return [
        {
            "name": "load_user_profile",
            "description": "Load the local user profile for Personal mode."
        },
        {
            "name": "save_user_profile",
            "description": "Save the local user profile for Personal mode."
        },
        {
            "name": "load_user_context",
            "description": "Load local manual user context."
        },
        {
            "name": "save_user_context",
            "description": "Save local manual user context."
        },
        {
            "name": "save_feedback",
            "description": "Save thumbs up/down feedback for evals and future training readiness."
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

    raise ValueError(f"Unknown tool: {tool_name}")
