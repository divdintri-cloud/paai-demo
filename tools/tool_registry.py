from tools.book_tool import get_book_library_summary, search_book_library
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
        {
            "name": "get_book_library_summary",
            "description": "Summarize the saved book library for the Literacy Agent.",
            "status": "Available",
            "safe_in_demo": "Yes",
            "connects_to": "books_inventory.csv",
            "output_type": "JSON summary",
        },
        {
            "name": "search_book_library",
            "description": "Search saved books by title, author, language, genre, or mood.",
            "status": "Available",
            "safe_in_demo": "Yes",
            "connects_to": "books_inventory.csv",
            "output_type": "JSON search results",
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

    if tool_name == "get_book_library_summary":
        return get_book_library_summary()

    if tool_name == "search_book_library":
        return search_book_library(arguments.get("query", ""))

    raise ValueError(f"Unknown tool: {tool_name}")
