from pathlib import Path
import json

import pandas as pd
import os
import streamlit as st

from skills.grocery_skills import (
    extract_grocery_items_from_photo,
    save_grocery_analysis,
    load_grocery_history_info,
    is_grocery_analysis_stale,
)
from skills.literacy_skills import (
    check_book_ownership,
    build_enriched_book_inventory,
    recommend_books_by_mood,
)
from skills.payment_skills import (
    ask_payment_agent,
    get_payment_summary,
    parse_uploaded_payment_file,
    save_payment_reminders,
)
from skills.activity_log import log_activity, get_recent_activity
from tools.feedback_tool import save_feedback
from tools.context_tool import load_user_context


# BOOKS_DB_PATH removed for Demo Mode; use get_books_inventory_path() instead

st.set_page_config(page_title="PAAI - Personal AI Assistant", layout="wide")


# --- PAAI COMPACT UI V1 ---
st.markdown(
    """
    <style>
    /* General compact layout */
    .block-container {
        padding-top: 1.2rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 100% !important;
    }

    /* Headings */
    h1 {
        font-size: 1.55rem !important;
        margin-bottom: 0.5rem !important;
    }

    h2 {
        font-size: 1.25rem !important;
        margin-bottom: 0.45rem !important;
    }

    h3 {
        font-size: 1.05rem !important;
        margin-bottom: 0.35rem !important;
    }

    p, li, label, div {
        font-size: 0.92rem;
    }

    /* Sidebar compact spacing */
    section[data-testid="stSidebar"] {
        min-width: 250px !important;
        max-width: 280px !important;
    }

    section[data-testid="stSidebar"] div {
        font-size: 0.9rem;
    }

    /* Buttons */
    .stButton button {
        padding: 0.35rem 0.55rem !important;
        font-size: 0.9rem !important;
        min-height: 2.1rem !important;
    }

    /* Inputs */
    textarea, input {
        font-size: 0.9rem !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
    }

    /* Expanders */
    details {
        font-size: 0.9rem !important;
    }

    /* Dataframes / tables */
    [data-testid="stDataFrame"] {
        font-size: 0.82rem !important;
    }

    /* Mobile/small screen */
    @media (max-width: 900px) {
        .block-container {
            padding-top: 0.8rem !important;
            padding-left: 0.7rem !important;
            padding-right: 0.7rem !important;
        }

        h1 {
            font-size: 1.35rem !important;
        }

        h2 {
            font-size: 1.12rem !important;
        }

        h3 {
            font-size: 1rem !important;
        }

        p, li, label, div {
            font-size: 0.86rem;
        }

        .stButton button {
            font-size: 0.84rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("PAAI - Personal AI Assistant")
st.write(
    "Choose an agent from the dropdown, or ask PAAI and it will route your question to the right specialist."
)

if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = "PAAI Home"

if st.session_state.selected_agent == "PAAI Assistant":
    st.session_state.selected_agent = "PAAI Home"

if "routed_question" not in st.session_state:
    st.session_state.routed_question = ""

if "literacy_action" not in st.session_state:
    st.session_state.literacy_action = "View my saved library"

if "payment_action" not in st.session_state:
    st.session_state.payment_action = "Payment dashboard"

demo_agent_options = [
    "PAAI Home",
    "Literacy Agent",
    "Payment Reminder Agent",
    "Grocery Help Agent",
    "User Profile",
    "Activity Log",
    "Evaluation Dashboard",
    "Entertainment Agent",
    "AI Product Manager Role Transition Agent",
    "Task & Planning Agent",
    "Travel Agent",
]

personal_agent_options = [
    "PAAI Home",
    "Literacy Agent",
    "Payment Reminder Agent",
    "Grocery Help Agent",
    "Activity Log",
    "Entertainment Agent",
    "AI Product Manager Role Transition Agent",
    "Task & Planning Agent",
    "Travel Agent",
]

agent_options = demo_agent_options if st.session_state.get("paai_mode", "Demo") == "Demo" else personal_agent_options


if st.session_state.selected_agent not in agent_options:
    st.session_state.selected_agent = "PAAI Home"

agent = st.sidebar.selectbox(
    "Choose an agent",
    agent_options,
    index=agent_options.index(st.session_state.selected_agent),
)

st.session_state.selected_agent = agent




def get_current_data_dir():
    mode = st.session_state.get("paai_mode", "Demo")
    return Path("demo_data") if mode == "Demo" else Path("data")


def get_books_inventory_path():
    return get_current_data_dir() / "books_inventory.csv"


def set_paai_data_environment():
    os.environ["PAAI_DATA_DIR"] = str(get_current_data_dir())


def safe_log_activity(user_question, routed_agent, action, result_summary):
    try:
        log_activity(
            user_question=user_question,
            routed_agent=routed_agent,
            action=action,
            result_summary=result_summary,
        )
    except Exception:
        pass

def get_current_data_dir():
    mode = st.session_state.get("paai_mode", "Demo")
    return Path("demo_data") if mode == "Demo" else Path("data")


def get_books_inventory_path():
    return get_current_data_dir() / "books_inventory.csv"


def get_grocery_latest_result_path():
    return get_current_data_dir() / "grocery_latest_result.json"


def set_paai_data_environment():
    os.environ["PAAI_DATA_DIR"] = str(get_current_data_dir())

def is_grocery_question(question):
    grocery_keywords = [
        "grocery",
        "groceries",
        "fridge",
        "pantry",
        "food",
        "shopping",
        "shopping list",
        "restock",
        "stock",
        "milk",
        "eggs",
        "rice",
        "atta",
        "dal",
        "curd",
        "yogurt",
        "banana",
        "apple",
        "tomato",
        "onion",
        "potato",
        "vegetable",
        "snack",
        "costco",
        "trader joe",
        "walmart",
        "indian grocery",
        "instacart",
        "door dash",
        "doordash",
    ]

    lower_question = question.lower()
    return any(keyword in lower_question for keyword in grocery_keywords)


def is_payment_question(question):
    payment_keywords = [
        "payment",
        "payments",
        "bill",
        "bills",
        "due",
        "overdue",
        "subscription",
        "subscriptions",
        "renewal",
        "paid",
        "amount",
        "credit card",
        "mortgage",
        "insurance",
    ]

    lower_question = question.lower()
    return any(keyword in lower_question for keyword in payment_keywords)


def is_add_book_question(question):
    add_book_keywords = [
        "add a book",
        "add book",
        "add this book",
        "add books",
        "upload a book",
        "upload book",
        "scan book",
        "scan books",
        "save a book",
        "save this book",
        "new book",
        "catalog book",
        "catalogue book",
        "inventory book",
    ]

    lower_question = question.lower()
    return any(keyword in lower_question for keyword in add_book_keywords)


def is_book_recommendation_question(question):
    recommendation_keywords = [
        "suggest a book",
        "recommend a book",
        "recommend books",
        "suggest books",
        "book based on mood",
        "based on mood",
        "what should i read",
        "what book should i read",
        "reading recommendation",
        "mood",
        "feel like reading",
    ]

    lower_question = question.lower()
    return any(keyword in lower_question for keyword in recommendation_keywords)


def is_book_ownership_question(question):
    book_keywords = [
        "do i own",
        "do we own",
        "is this book in my library",
        "is this in my library",
        "in my library",
        "book",
        "books",
        "author",
    ]

    lower_question = question.lower()
    return any(keyword in lower_question for keyword in book_keywords)


def extract_mood_from_question(question):
    lower_question = question.lower()

    mood_words = [
        "motivated",
        "focused",
        "reflective",
        "calm",
        "happy",
        "sad",
        "empowered",
        "inspired",
        "career growth",
        "light",
        "easy",
        "deep",
        "spiritual",
        "productive",
    ]

    for mood in mood_words:
        if mood in lower_question:
            return mood

    return "Reflective"


def clean_book_query(question):
    cleaned = (
        question
        .replace("Do I own", "")
        .replace("do I own", "")
        .replace("do i own", "")
        .replace("Do we own", "")
        .replace("do we own", "")
        .replace("Is", "")
        .replace("is", "")
        .replace("in my library", "")
        .replace("in our library", "")
        .replace("?", "")
        .strip()
    )

    return cleaned




def show_grocery_result(result):
    st.subheader("Grocery Summary")
    st.write(result.get("summary", ""))

    visible_items = result.get("visible_items", [])
    running_low = result.get("running_low", [])
    shopping_list = result.get("shopping_list", [])
    manual_check = result.get("manual_check", [])
    photo_quality = result.get("photo_quality", {})
    shopping_message = result.get("shopping_message", "")

    if photo_quality:
        st.subheader("Photo Quality")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Photo score", photo_quality.get("score", 0))

        with col2:
            st.write(photo_quality.get("suggestion", ""))

    if visible_items:
        st.subheader("Visible Items")
        st.dataframe(visible_items, use_container_width=True)

    if running_low:
        st.subheader("Running Low")
        st.dataframe(running_low, use_container_width=True)

    if shopping_list:
        st.subheader("Suggested Shopping List")
        st.dataframe(shopping_list, use_container_width=True)

    if manual_check:
        st.subheader("Manual Check")
        st.dataframe(manual_check, use_container_width=True)

    if shopping_message:
        st.subheader("Copyable Shopping Message")
        st.text_area("Shopping list message", value=shopping_message, height=220)

        st.download_button(
            label="Download Shopping List",
            data=shopping_message,
            file_name="shopping_list.txt",
            mime="text/plain",
        )


def show_grocery_agent(default_question="What groceries do I need to restock?"):
    st.header("Grocery Help Agent")

    st.write(
        "Upload a fridge, pantry, grocery, or receipt photo. "
        "PAAI can identify visible items, running-low items, shopping suggestions, and manual checks."
    )

    uploaded_grocery_photo = st.file_uploader(
        "Upload grocery/fridge/pantry image",
        type=["jpg", "jpeg", "png"],
        key="grocery_upload",
    )

    if uploaded_grocery_photo:
        st.image(
            uploaded_grocery_photo,
            caption="Uploaded grocery photo",
            use_container_width=True,
        )

    if st.button("Analyze Groceries", key="analyze_groceries"):
        if uploaded_grocery_photo is None:
            st.warning("Please upload a grocery, fridge, pantry, or receipt photo first.")
            return

        with st.spinner("Analyzing grocery photo..."):
            result = extract_grocery_items_from_photo(uploaded_grocery_photo)

        saved_result = save_grocery_analysis(result)

        st.success("New grocery photo analyzed and saved.")
        st.caption(f"Analyzed at: {saved_result.get('analyzed_at', '')}")

        show_grocery_result(saved_result)

    st.subheader("Use Previous Grocery Analysis")

    if st.button("Answer from Saved Grocery Analysis", key="use_saved_grocery"):
        history_info = load_grocery_history_info()

        if not history_info.get("has_history"):
            st.warning(
                "I do not have a previous grocery photo analysis yet. "
                "Upload a grocery photo first."
            )
            return

        first_uploaded_at = history_info["first_uploaded_at"]
        last_uploaded_at = history_info["last_uploaded_at"]
        latest_result = history_info["latest_result"]

        is_stale, age_days = is_grocery_analysis_stale(last_uploaded_at, stale_after_days=3)

        st.info(f"First grocery photo analysis: {first_uploaded_at}")
        st.info(f"Most recent grocery photo analysis: {last_uploaded_at}")

        if is_stale:
            st.warning(
                f"Your latest grocery photo analysis is {age_days} day(s) old. "
                "Upload a new photo if your fridge or pantry has changed."
            )
        else:
            st.success("Using your recent saved grocery analysis.")

        show_grocery_result(latest_result)



def show_payment_upload_flow():
    st.subheader("Upload Payment Details or Bills")

    mode = st.session_state.get("paai_mode", "Demo")

    if mode == "Demo":
        st.warning(
            "Demo mode: do not upload real bills, bank statements, account numbers, "
            "card numbers, IDs, addresses, or sensitive financial documents."
        )
    else:
        st.warning(
            "For safety, upload only cleaned payment reminder files. Avoid account numbers, "
            "card numbers, transaction IDs, full addresses, and sensitive notes."
        )

    uploaded_file = st.file_uploader(
        "Upload payment reminders as CSV, Excel, or Word document",
        type=["csv", "xlsx", "xls", "docx"],
        key=f"payment_upload_{mode}",
    )

    if "draft_payment_import" not in st.session_state:
        st.session_state.draft_payment_import = None

    if uploaded_file:
        st.write(f"Uploaded file: {uploaded_file.name}")

        if st.button("Preview Payment Reminders", key=f"preview_payment_import_{mode}"):
            with st.spinner("Reading uploaded file and preparing draft reminders..."):
                draft_df = parse_uploaded_payment_file(uploaded_file)

            st.session_state.draft_payment_import = draft_df

    if st.session_state.draft_payment_import is not None:
        draft_df = st.session_state.draft_payment_import

        st.subheader("Draft Payment Reminders")
        st.write(f"Rows found: {len(draft_df)}")
        st.dataframe(draft_df, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Save Draft to Payment Reminders", key=f"save_payment_import_{mode}"):
                saved_df = save_payment_reminders(draft_df)

                try:
                    log_activity(
                        user_question="Upload payment details or bills",
                        routed_agent="Payment Reminder Agent",
                        action="Save payment reminders",
                        result_summary=f"Saved {len(draft_df)} uploaded payment reminder row(s).",
                    )
                except Exception:
                    pass

                st.success(f"Saved. You now have {len(saved_df)} payment reminder rows.")

        with col2:
            if st.button("Clear Draft Import", key=f"clear_payment_import_{mode}"):
                st.session_state.draft_payment_import = None
                st.success("Draft import cleared.")
                st.rerun()

        csv_data = draft_df.to_csv(index=False)

        st.download_button(
            label="Download Draft Import CSV",
            data=csv_data,
            file_name="draft_payment_reminders.csv",
            mime="text/csv",
        )



def show_payment_agent(question="What payments are due soon?"):
    st.header("Payment Reminder Agent")

    payment_data = get_payment_summary()
    summary = payment_data["summary"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total payments", summary["total_payments"])

    with col2:
        st.metric("Due soon", summary["due_soon_count"])

    with col3:
        st.metric("Overdue", summary["overdue_count"])

    with col4:
        st.metric("Pending amount", f"${summary['total_pending_amount']:,.2f}")

    payment_question = st.text_input(
        "Ask a payment question",
        value=question,
        key="payment_question",
    )

    if st.button("Ask Payment Reminder Agent"):
        with st.spinner("Checking payment reminders..."):
            answer = ask_payment_agent(payment_question)

        st.write(answer)

    with st.expander("Show due soon payments"):
        due_soon_df = payment_data["due_soon"]
        if due_soon_df.empty:
            st.info("No unpaid payments due soon.")
        else:
            st.dataframe(due_soon_df, use_container_width=True)

    with st.expander("Show overdue payments"):
        overdue_df = payment_data["overdue"]
        if overdue_df.empty:
            st.success("No overdue unpaid payments.")
        else:
            st.dataframe(overdue_df, use_container_width=True)

    with st.expander("Show subscriptions"):
        subscriptions_df = payment_data["subscriptions"]
        if subscriptions_df.empty:
            st.info("No subscriptions found.")
        else:
            st.dataframe(subscriptions_df, use_container_width=True)




def is_payment_import_question(question):
    keywords = [
        "import payment",
        "import payments",
        "upload payment",
        "upload payments",
        "payment file",
        "expense file",
        "upload expense",
        "import expense",
        "excel payment",
        "excel expense",
        "word payment",
        "payment reminder file",
    ]

    lower_question = question.lower()
    return any(keyword in lower_question for keyword in keywords)


def is_library_view_question(question):
    keywords = [
        "show my library",
        "view my library",
        "open my library",
        "library inventory",
        "book inventory",
        "show saved books",
        "view saved books",
    ]

    lower_question = question.lower()
    return any(keyword in lower_question for keyword in keywords)


def is_list_books_question(question):
    keywords = [
        "list all books",
        "show all books",
        "all books",
        "book list",
        "list books",
    ]

    lower_question = question.lower()
    return any(keyword in lower_question for keyword in keywords)


def is_duplicate_check_question(question):
    keywords = [
        "check duplicate",
        "check duplicates",
        "duplicate books",
        "duplicates in library",
        "find duplicate",
        "find duplicates",
        "merge duplicate",
        "merge duplicates",
    ]

    lower_question = question.lower()
    return any(keyword in lower_question for keyword in keywords)



def render_home_tile(title, main_value, detail_1, detail_2, background_color, border_color, emoji=""):
    title = display_value(title)
    main_value = display_value(main_value)
    detail_1 = display_value(detail_1)
    detail_2 = display_value(detail_2)

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {background_color}, #ffffff);
            border: 1px solid rgba(0,0,0,0.06);
            border-left: 7px solid {border_color};
            padding: 18px 18px 16px 18px;
            border-radius: 18px;
            min-height: 165px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            ">
                <div style="font-size: 14px; font-weight: 800; color: #374151;">
                    {title}
                </div>
                <div style="font-size: 24px;">
                    {emoji}
                </div>
            </div>
            <div style="font-size: 26px; font-weight: 900; color: #111827; margin-bottom: 10px;">
                {main_value}
            </div>
            <div style="font-size: 12.5px; line-height: 1.55; color: #4b5563;">
                {detail_1}<br>
                {detail_2}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def route_home_question(home_question):
    if not home_question.strip():
        st.warning("Please type a question first.")
        return

    st.session_state.routed_question = home_question

    if is_grocery_question(home_question):
        log_activity(
            user_question=home_question,
            routed_agent="Grocery Help Agent",
            action="Redirect",
            result_summary="Routed grocery-related question from PAAI Home.",
        )
        st.session_state.selected_agent = "Grocery Help Agent"
        st.rerun()

    elif is_payment_import_question(home_question):
        log_activity(
            user_question=home_question,
            routed_agent="Payment Reminder Agent",
            action="Redirect",
            result_summary="Routed payment import request from PAAI Home.",
        )
        st.session_state.selected_agent = "Payment Reminder Agent"
        st.session_state.payment_action = "Import payment file"
        st.rerun()

    elif is_payment_question(home_question):
        log_activity(
            user_question=home_question,
            routed_agent="Payment Reminder Agent",
            action="Redirect",
            result_summary="Routed payment-related question from PAAI Home.",
        )
        st.session_state.selected_agent = "Payment Reminder Agent"
        st.session_state.payment_action = "Payment dashboard"
        st.rerun()

    elif is_add_book_question(home_question):
        log_activity(
            user_question=home_question,
            routed_agent="Literacy Agent",
            action="Redirect",
            result_summary="Routed add-book request from PAAI Home.",
        )
        st.session_state.selected_agent = "Literacy Agent"
        st.session_state.literacy_action = "Add book from photo"
        st.rerun()

    elif is_book_recommendation_question(home_question):
        log_activity(
            user_question=home_question,
            routed_agent="Literacy Agent",
            action="Redirect",
            result_summary="Routed book recommendation request from PAAI Home.",
        )
        st.session_state.selected_agent = "Literacy Agent"
        st.session_state.literacy_action = "Recommend books by mood"
        st.rerun()

    elif is_duplicate_check_question(home_question):
        log_activity(
            user_question=home_question,
            routed_agent="Literacy Agent",
            action="Redirect",
            result_summary="Routed duplicate-check request from PAAI Home.",
        )
        st.session_state.selected_agent = "Literacy Agent"
        st.session_state.literacy_action = "Duplicate check"
        st.rerun()

    elif is_list_books_question(home_question):
        log_activity(
            user_question=home_question,
            routed_agent="Literacy Agent",
            action="Redirect",
            result_summary="Routed list-books request from PAAI Home.",
        )
        st.session_state.selected_agent = "Literacy Agent"
        st.session_state.literacy_action = "List all books"
        st.rerun()

    elif is_library_view_question(home_question):
        log_activity(
            user_question=home_question,
            routed_agent="Literacy Agent",
            action="Redirect",
            result_summary="Routed library view request from PAAI Home.",
        )
        st.session_state.selected_agent = "Literacy Agent"
        st.session_state.literacy_action = "View my saved library"
        st.rerun()

    elif is_book_ownership_question(home_question):
        log_activity(
            user_question=home_question,
            routed_agent="Literacy Agent",
            action="Redirect",
            result_summary="Routed book ownership request from PAAI Home.",
        )
        st.session_state.selected_agent = "Literacy Agent"
        st.session_state.literacy_action = "Check if I own a book"
        st.rerun()

    else:
        st.info(
            "I can currently route grocery, payment, and book questions. "
            "Try: 'Show my library', 'What payments are due soon?', or 'What groceries do I need to restock?'"
        )



def display_value(value, fallback="Data not available"):
    if value is None:
        return fallback

    value_text = str(value).strip()

    if value_text == "" or value_text.lower() in ["nan", "none", "not available"]:
        return fallback

    return value_text


# --- PAAI HOME PERSONALIZATION V1 ---
def get_paai_display_name():
    display_name = st.session_state.get("paai_display_name", "").strip()
    if display_name:
        return display_name

    if st.session_state.get("paai_mode", "Demo") == "Demo":
        return "there"

    try:
        profile = load_divya_profile()
        return profile.get("name", "there")
    except Exception:
        return "there"


def get_paai_home_recommendations():
    mode = st.session_state.get("paai_mode", "Demo")

    if mode == "Demo":
        return [
            "Explore each agent from the sidebar.",
            "Try one book, grocery, or payment question.",
            "Use thumbs feedback after testing.",
            "Avoid uploading private or sensitive files in Demo mode.",
        ]

    context = load_user_context()
    priorities = context.get("current_priorities", [])
    short_term_goals = context.get("short_term_goals", [])

    recommendations = []

    for item in priorities[:2]:
        recommendations.append(item)

    for item in short_term_goals[:2]:
        if item not in recommendations:
            recommendations.append(item)

    if not recommendations:
        recommendations = [
            "Review eval test cases.",
            "Collect useful feedback.",
            "Update user context.",
            "Continue building PAAI as a portfolio project.",
        ]

    return recommendations[:4]


def show_personalized_home_intro():
    mode = st.session_state.get("paai_mode", "Demo")
    display_name = get_paai_display_name()

    try:
        wish = get_time_based_wish()
    except Exception:
        wish = "Welcome"

    if mode == "Demo":
        st.markdown(f"### {wish}, {display_name} 👋")
        st.caption("Welcome to PAAI Demo. This mode uses generic safe context and does not show personal profile details.")
    else:
        st.markdown(f"### {wish}, {display_name} 👋")
        st.caption("Here’s your PAAI 1.0 personal command center.")

    recommendations = get_paai_home_recommendations()

    with st.expander("Recommended next actions", expanded=True):
        for index, item in enumerate(recommendations, start=1):
            st.write(f"{index}. {item}")



def show_paai_home():
    show_personalized_home_intro()
    st.divider()

    st.header("PAAI Home")

    mode = st.session_state.get("paai_mode", "Demo")

    if mode == "Demo":
        st.warning(
            "Demo Mode: safe sharing version. Book, payment, and grocery uploads may be processed by AI. "
            "Please do not upload sensitive images, IDs, private documents, bank statements, payment screenshots, or personal records."
        )

    st.markdown(
        f"""
        <div style="font-size: 13px; color: #555; margin-bottom: 16px;">
            Mode: <b>{mode}</b>. Quick overview across available PAAI tools.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Books summary
    try:
        books_df = load_saved_books()
    except Exception:
        books_df = pd.DataFrame()

    if books_df is None:
        books_df = pd.DataFrame()

    if books_df.empty:
        books_main = "Data not available"
        books_detail_1 = "No saved books found"
        books_detail_2 = "Upload a book photo to generate summary"
    else:
        books_main = f"{len(books_df)} books"

        if "Language" in books_df.columns:
            language_count = books_df["Language"].fillna("Unclear").astype(str).nunique()
            books_detail_1 = f"{language_count} language(s)"
        else:
            books_detail_1 = "Language data not available"

        try:
            duplicate_count = len(find_duplicate_books(books_df))
        except Exception:
            duplicate_count = 0

        books_detail_2 = f"{duplicate_count} duplicate row(s)"

    # Payment summary
    try:
        payment_data = get_payment_summary()
        payment_summary = payment_data.get("summary", {})

        due_soon_count = payment_summary.get("due_soon_count", 0)
        overdue_count = payment_summary.get("overdue_count", 0)
        total_pending_amount = payment_summary.get("total_pending_amount", 0)

        if due_soon_count == 0 and overdue_count == 0 and float(total_pending_amount or 0) == 0:
            payment_main = "Data not available"
            payment_detail_1 = "No payment reminders found"
            payment_detail_2 = "Upload payment details to generate summary"
        else:
            payment_main = f"{due_soon_count} due soon"
            payment_detail_1 = f"{overdue_count} overdue"
            payment_detail_2 = f"${float(total_pending_amount or 0):,.2f} pending"

    except Exception:
        payment_main = "Data not available"
        payment_detail_1 = "No payment summary available"
        payment_detail_2 = "Upload payment details to generate summary"

    # Grocery summary
    try:
        grocery_info = load_grocery_history_info()
    except Exception:
        grocery_info = {"has_history": False, "latest_result": {}}

    latest_result = grocery_info.get("latest_result", {}) if isinstance(grocery_info, dict) else {}

    if not grocery_info.get("has_history") or not latest_result:
        groceries_main = "Data not available"
        groceries_detail_1 = "No grocery summary available"
        groceries_detail_2 = "Upload a grocery photo to generate summary"
        grocery_color = "#fff7ed"
        grocery_border = "#f97316"
    else:
        shopping_count = len(latest_result.get("shopping_list", []))
        manual_count = len(latest_result.get("manual_check", []))

        if shopping_count == 0 and manual_count == 0:
            groceries_main = "Data not available"
            groceries_detail_1 = "No grocery summary available"
            groceries_detail_2 = "Upload a grocery photo to generate summary"
            grocery_color = "#fff7ed"
            grocery_border = "#f97316"
        else:
            groceries_main = f"{shopping_count} suggestions"
            groceries_detail_1 = f"Last analyzed: {grocery_info.get('last_uploaded_at', 'Data not available')}"
            groceries_detail_2 = f"{manual_count} manual check(s)"
            grocery_color = "#ecfdf5"
            grocery_border = "#10b981"

    col1, col2, col3 = st.columns(3)

    with col1:
        render_home_tile(
            title="Books",
            main_value=books_main,
            detail_1=books_detail_1,
            detail_2=books_detail_2,
            background_color="#eff6ff",
            border_color="#3b82f6",
            emoji="📚",
        )

    with col2:
        render_home_tile(
            title="Payment Reminders",
            main_value=payment_main,
            detail_1=payment_detail_1,
            detail_2=payment_detail_2,
            background_color="#f5f3ff",
            border_color="#8b5cf6",
            emoji="💳",
        )

    with col3:
        render_home_tile(
            title="Groceries",
            main_value=groceries_main,
            detail_1=groceries_detail_1,
            detail_2=groceries_detail_2,
            background_color=grocery_color,
            border_color=grocery_border,
            emoji="🛒",
        )

    st.divider()

    st.subheader("Ask PAAI")

    prompt_label = (
        "Ask me about books, payment reminders, or grocery list"
    )

    home_question = st.text_input(
        prompt_label,
        value="",
        key="home_paai_question",
    )

    if st.button("Ask PAAI from Home"):
        route_home_question(home_question)

    st.divider()

    st.subheader("Recent Log Updates")

    try:
        recent_df = get_recent_activity(limit=5)
    except Exception:
        recent_df = pd.DataFrame()

    if recent_df.empty:
        st.info("Data not available")
    else:
        st.dataframe(recent_df, use_container_width=True)



def load_saved_books():
    books_path = get_books_inventory_path()

    if not books_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(books_path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def save_books_to_library(books):
    books_path = get_books_inventory_path()
    books_path.parent.mkdir(exist_ok=True)

    if isinstance(books, dict):
        books = books.get("books", [])

    if books is None:
        books = []

    new_books_df = pd.DataFrame(books)

    if new_books_df.empty:
        return load_saved_books()

    existing_df = load_saved_books()

    if existing_df.empty:
        combined_df = new_books_df
    else:
        combined_df = pd.concat([existing_df, new_books_df], ignore_index=True)

    combined_df.to_csv(books_path, index=False)

    return combined_df


def find_duplicate_books(df=None):
    if df is None:
        df = load_saved_books()

    if df.empty or "Title" not in df.columns:
        return pd.DataFrame()

    temp_df = df.copy()
    temp_df["Title Clean"] = temp_df["Title"].fillna("").astype(str).str.lower().str.strip()

    duplicates_df = temp_df[temp_df.duplicated("Title Clean", keep=False)]

    return duplicates_df.drop(columns=["Title Clean"], errors="ignore")


def get_subject_dashboard():
    df = load_saved_books()

    if df.empty:
        return pd.DataFrame()

    subject_column = None

    for column in ["Genre", "Online Categories", "Mood Fit", "Language"]:
        if column in df.columns:
            subject_column = column
            break

    if not subject_column:
        return pd.DataFrame()

    dashboard = (
        df[subject_column]
        .fillna("Unclear")
        .astype(str)
        .value_counts()
        .reset_index()
    )

    dashboard.columns = ["Subject / Category", "Book Count"]

    return dashboard


def show_library_summary():
    st.subheader("Saved Library")

    df = load_saved_books()

    if df.empty:
        st.info("No saved books found yet.")
        return

    st.metric("Total books", len(df))
    st.caption(f"Library file: {get_books_inventory_path()}")
    st.dataframe(df, use_container_width=True)


def show_all_books():
    st.subheader("All Books")

    df = load_saved_books()

    if df.empty:
        st.info("No saved books found yet.")
        return

    display_columns = [
        col for col in [
            "Title",
            "Display Title",
            "Original Title",
            "Translated Title",
            "Author",
            "Language",
            "Genre",
            "Mood Fit",
            "Energy Level",
            "Extraction Confidence",
            "Status",
        ]
        if col in df.columns
    ]

    if display_columns:
        st.dataframe(df[display_columns], use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)


def show_duplicate_check():
    st.subheader("Duplicate Check")

    duplicates_df = find_duplicate_books()

    if duplicates_df.empty:
        st.success("No duplicate rows found.")
        return

    st.warning(f"Found {len(duplicates_df)} possible duplicate row(s).")
    st.dataframe(duplicates_df, use_container_width=True)


def show_subject_dashboard_only():
    st.subheader("Subject Dashboard")

    dashboard = get_subject_dashboard()

    if dashboard.empty:
        st.info("No subject or category summary available yet.")
        return

    st.dataframe(dashboard, use_container_width=True)


def show_book_ownership():
    st.subheader("Check if I Own a Book")

    query = st.text_input(
        "Enter a book title or author",
        value="",
        key="book_ownership_query",
    )

    if st.button("Check Library", key="check_book_ownership_button"):
        if not query.strip():
            st.warning("Please enter a book title or author.")
            return

        set_paai_data_environment()

        result = check_book_ownership(query)

        if result.get("owned"):
            st.success(result.get("message", "Book found."))
        else:
            st.info(result.get("message", "Book not found."))

        matches = result.get("matches", [])

        if matches:
            st.dataframe(pd.DataFrame(matches), use_container_width=True)


def show_add_book_flow():
    st.subheader("Add Book from Photo")

    set_paai_data_environment()

    mode = st.session_state.get("paai_mode", "Demo")
    library_path = get_books_inventory_path()

    st.caption(f"Mode: {mode} · Saving to: {library_path}")

    uploaded_files = st.file_uploader(
        "Upload one or more book photos",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"book_photo_upload_{mode}",
    )

    if "pending_extracted_books" not in st.session_state:
        st.session_state.pending_extracted_books = []

    if st.button("Extract Book Information", key=f"extract_books_button_{mode}"):
        if not uploaded_files:
            st.warning("Please upload at least one book photo first.")
            return

        with st.spinner("Extracting book information..."):
            result = build_enriched_book_inventory(uploaded_files)

        if isinstance(result, dict) and result.get("error"):
            st.error(result.get("error"))
            st.write(result.get("raw_output", ""))
            return

        if isinstance(result, dict):
            books = result.get("books", [])
            summary = result.get("collection_summary", "")
        elif isinstance(result, list):
            books = result
            summary = ""
        else:
            books = []
            summary = ""

        if not books:
            st.warning("No books were extracted.")
            return

        st.session_state.pending_extracted_books = books
        st.session_state.pending_collection_summary = summary

        st.success(f"Extracted {len(books)} book(s). Review below, then save.")

    pending_books = st.session_state.get("pending_extracted_books", [])

    if pending_books:
        st.subheader("Extracted Book Preview")

        summary = st.session_state.get("pending_collection_summary", "")
        if summary:
            st.caption(summary)

        st.dataframe(pd.DataFrame(pending_books), use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Save Extracted Books to Library", key=f"save_books_button_{mode}"):
                saved_df = save_books_to_library(pending_books)

                try:
                    log_activity(
                        user_question="Add book from photo",
                        routed_agent="Literacy Agent",
                        action="Save books",
                        result_summary=f"Saved {len(pending_books)} book(s) to {library_path}.",
                    )
                except Exception:
                    pass

                st.success(f"Saved {len(pending_books)} book(s). Total rows: {len(saved_df)}")
                st.caption(f"Saved to: {library_path}")

                st.session_state.pending_extracted_books = []
                st.session_state.pending_collection_summary = ""

                st.rerun()

        with col2:
            if st.button("Clear Preview", key=f"clear_books_button_{mode}"):
                st.session_state.pending_extracted_books = []
                st.session_state.pending_collection_summary = ""
                st.rerun()


def show_book_recommendations():
    st.subheader("Mood-Based Book Recommendations")

    df = load_saved_books()

    if df.empty:
        st.info("No saved books found yet. Add books first, then try recommendations.")
        return

    mood = st.text_input(
        "What mood are you in?",
        placeholder="Example: empowered, focused, calm, motivated",
        key="book_recommendation_mood",
    )

    if st.button("Recommend Books", key="recommend_books_button"):
        if not mood.strip():
            st.warning("Please enter a mood first.")
            return

        books_context = df.to_json(orient="records", force_ascii=False)

        with st.spinner("Finding recommendations from your saved library..."):
            raw_output = recommend_books_by_mood(mood, books_context)

        try:
            parsed = json.loads(raw_output)
            recommendations = parsed.get("recommendations", [])
        except Exception:
            st.write(raw_output)
            return

        if not recommendations:
            st.info("No recommendations returned.")
            return

        for rec in recommendations:
            title = rec.get("title", "Untitled")
            author = rec.get("author", "Unknown author")
            why = rec.get("why_this_fits", "")
            confidence = rec.get("confidence_note", "")
            language = rec.get("language", "")
            genre = rec.get("genre_or_subject", "")
            thumbnail = rec.get("thumbnail", "")

            with st.container():
                cols = st.columns([1, 4])

                with cols[0]:
                    if thumbnail:
                        st.image(thumbnail, width=90)

                with cols[1]:
                    st.markdown(f"**{title}**")
                    st.write(f"Author: {author}")

                    if language or genre:
                        st.caption(f"{language} · {genre}")

                    if why:
                        st.write(why)

                    if confidence:
                        st.caption(confidence)


def show_literacy_agent_tabs():
    st.header("Literacy Agent")

    set_paai_data_environment()

    st.caption(
        f"Mode: {st.session_state.get('paai_mode', 'Demo')} · "
        f"Library file: {get_books_inventory_path()}"
    )

    library_tab, mood_tab = st.tabs(["Library", "Mood Recommendations"])

    with library_tab:
        library_actions = [
            "View my saved library",
            "List all books",
            "Add book from photo",
            "Check if I own a book",
            "Duplicate check",
            "Subject dashboard",
        ]

        default_action = st.session_state.get("literacy_action", "View my saved library")

        if default_action not in library_actions:
            default_action = "View my saved library"

        library_action = st.selectbox(
            "Choose a library action",
            library_actions,
            index=library_actions.index(default_action),
            key="literacy_library_action",
        )

        st.session_state.literacy_action = library_action

        if library_action == "View my saved library":
            show_library_summary()

        elif library_action == "List all books":
            show_all_books()

        elif library_action == "Add book from photo":
            show_add_book_flow()

        elif library_action == "Check if I own a book":
            show_book_ownership()

        elif library_action == "Duplicate check":
            show_duplicate_check()

        elif library_action == "Subject dashboard":
            show_subject_dashboard_only()

    with mood_tab:
        show_book_recommendations()




def get_eval_cases_path():
    return Path("evals") / "paai_eval_cases.csv"


def load_eval_cases():
    eval_path = get_eval_cases_path()

    if not eval_path.exists():
        return pd.DataFrame(
            columns=[
                "Test Name",
                "User Input",
                "Expected Agent",
                "Expected Behavior",
                "Status",
                "Notes",
            ]
        )

    try:
        return pd.read_csv(eval_path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(
            columns=[
                "Test Name",
                "User Input",
                "Expected Agent",
                "Expected Behavior",
                "Status",
                "Notes",
            ]
        )


def save_eval_cases(eval_df):
    eval_path = get_eval_cases_path()
    eval_path.parent.mkdir(exist_ok=True)
    eval_df.to_csv(eval_path, index=False)


def show_evaluation_dashboard():
    st.header("PAAI Evaluation Dashboard")

    st.write(
        "Use this dashboard to manually test whether PAAI routes correctly, protects demo data, "
        "and produces the expected behavior."
    )

    eval_df = load_eval_cases()

    if eval_df.empty:
        st.info("No eval cases found.")
        return

    st.subheader("Eval Cases")

    edited_df = st.data_editor(
        eval_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Not run", "Pass", "Fail", "Needs review"],
                required=True,
            )
        },
        key="paai_eval_cases_editor",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        pass_count = len(edited_df[edited_df["Status"] == "Pass"]) if "Status" in edited_df.columns else 0
        st.metric("Pass", pass_count)

    with col2:
        fail_count = len(edited_df[edited_df["Status"] == "Fail"]) if "Status" in edited_df.columns else 0
        st.metric("Fail", fail_count)

    with col3:
        not_run_count = len(edited_df[edited_df["Status"] == "Not run"]) if "Status" in edited_df.columns else 0
        st.metric("Not run", not_run_count)

    if st.button("Save Eval Results"):
        save_eval_cases(edited_df)

        try:
            log_activity(
                user_question="Update evaluation dashboard",
                routed_agent="Evaluation Dashboard",
                action="Save eval results",
                result_summary=f"Saved {len(edited_df)} evaluation case(s).",
            )
        except Exception:
            pass

        st.success("Eval results saved.")

    st.divider()

    st.subheader("How to use this")

    st.write("1. Open each test case.")
    st.write("2. Perform the action in PAAI.")
    st.write("3. Mark the result as Pass, Fail, or Needs review.")
    st.write("4. Add notes for anything broken or confusing.")
    st.write("5. Save eval results.")



def get_divya_profile_path():
    return Path("data") / "divya_profile.json"


def load_divya_profile():
    profile_path = get_divya_profile_path()

    default_profile = {
        "name": "User",
        "timezone": "America/Chicago",
        "primary_goal": "Transition into an AI Product Manager role",
        "preferred_style": "Step-by-step, practical, beginner-friendly",
        "privacy_preference": "Keep personal data local",
        "current_project": "PAAI 1.0",
        "career_focus": "AI Product Manager role transformation",
        "learning_focus": "LLMs, agents, evals, personalization, product strategy",
        "response_preference": "Clear instructions with commands, checkpoints, and careful changes",
        "notes": "PAAI should act as Divya's personal assistant while keeping Demo mode generic and safe.",
    }

    if not profile_path.exists():
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(json.dumps(default_profile, indent=2), encoding="utf-8")
        return default_profile

    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        return default_profile


def save_divya_profile(profile):
    profile_path = get_divya_profile_path()
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")


def show_divya_profile():
    st.header("User Profile")

    st.caption(
        "This is PAAI's personalization layer. It stores Divya-specific context locally "
        "so PAAI can become more personal over time."
    )

    if st.session_state.get("paai_mode", "Demo") == "Demo":
        st.info("Demo mode uses a generic safe profile. Divya's personal profile is hidden.")

        st.subheader("Demo Profile")
        st.write("**Name:** Demo User")
        st.write("**Primary goal:** Explore PAAI safely")
        st.write("**Current project:** PAAI Demo")
        st.write("**Preferred style:** Clear, helpful, beginner-friendly responses")
        st.caption("Personal profile data is only available in Personal mode on Divya's local machine.")
        return

    profile = load_divya_profile()

    st.subheader("Edit Personal Profile")

    name = st.text_input("Name", value=profile.get("name", "User"))
    timezone = st.text_input("Timezone", value=profile.get("timezone", "America/Chicago"))
    primary_goal = st.text_area("Primary goal", value=profile.get("primary_goal", ""))
    preferred_style = st.text_area("Preferred response style", value=profile.get("preferred_style", ""))
    privacy_preference = st.text_area("Privacy preference", value=profile.get("privacy_preference", ""))
    current_project = st.text_input("Current project", value=profile.get("current_project", "PAAI 1.0"))
    career_focus = st.text_area("Career focus", value=profile.get("career_focus", ""))
    learning_focus = st.text_area("Learning focus", value=profile.get("learning_focus", ""))
    response_preference = st.text_area("Response preference", value=profile.get("response_preference", ""))
    notes = st.text_area("Notes", value=profile.get("notes", ""))

    updated_profile = {
        "name": name,
        "timezone": timezone,
        "primary_goal": primary_goal,
        "preferred_style": preferred_style,
        "privacy_preference": privacy_preference,
        "current_project": current_project,
        "career_focus": career_focus,
        "learning_focus": learning_focus,
        "response_preference": response_preference,
        "notes": notes,
    }

    if st.button("Save User Profile", use_container_width=True):
        save_divya_profile(updated_profile)

        try:
            log_activity(
                user_question="Update User Profile",
                routed_agent="User Profile",
                action="Save profile",
                result_summary="Updated local personalization profile.",
            )
        except Exception:
            pass

        st.success("User Profile saved.")

    st.divider()

    st.subheader("Raw Profile JSON")
    st.json(updated_profile)


if agent == "PAAI Home":
    show_paai_home()


elif agent == "Grocery Help Agent":
    show_grocery_agent()

elif agent == "Payment Reminder Agent":
    st.header("Payment Reminder Agent")

    dashboard_tab, upload_tab = st.tabs(["Dashboard", "Upload Payment Details / Bills"])

    with dashboard_tab:
        routed_question = st.session_state.get("routed_question", "")
        if routed_question:
            st.caption(f"Routed question: {routed_question}")
            show_payment_agent(routed_question)
        else:
            show_payment_agent()

    with upload_tab:
        show_payment_upload_flow()


elif agent == "Literacy Agent":
    show_literacy_agent_tabs()


elif agent == "Evaluation Dashboard":
    show_evaluation_dashboard()


elif agent == "User Profile":
    show_divya_profile()

elif agent == "Activity Log":
    st.header("PAAI Activity Log")

    recent_df = get_recent_activity(limit=20)

    if recent_df.empty:
        st.info("No activity logged yet.")
    else:
        st.dataframe(recent_df, use_container_width=True)

        csv_data = recent_df.to_csv(index=False)

        st.download_button(
            label="Download Recent Activity Log",
            data=csv_data,
            file_name="paai_activity_log_recent.csv",
            mime="text/csv",
        )

else:
    st.header(agent)
    st.info("This agent will be added later.")


# --- PAAI FEEDBACK WIDGET V1 ---
st.divider()
st.subheader("Feedback")

st.caption("Help improve PAAI by marking whether this page or response was useful.")

feedback_col1, feedback_col2 = st.columns(2)

if "paai_feedback_choice" not in st.session_state:
    st.session_state.paai_feedback_choice = ""

with feedback_col1:
    if st.button("👍 Helpful", use_container_width=True):
        st.session_state.paai_feedback_choice = "Yes"

with feedback_col2:
    if st.button("👎 Needs improvement", use_container_width=True):
        st.session_state.paai_feedback_choice = "No"

feedback_notes = st.text_area(
    "Correction notes",
    placeholder="What should PAAI improve?",
    key="paai_feedback_notes",
)

ideal_answer = st.text_area(
    "Ideal answer",
    placeholder="Optional: write what the better answer should have been.",
    key="paai_ideal_answer",
)

if st.button("Save Feedback", use_container_width=True):
    if not st.session_state.paai_feedback_choice:
        st.warning("Please select Helpful or Needs improvement first.")
    else:
        from datetime import datetime
        import csv
        from pathlib import Path

        feedback_path = Path("evals") / "paai_feedback_log.csv"
        feedback_path.parent.mkdir(parents=True, exist_ok=True)

        file_exists = feedback_path.exists()

        with feedback_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if not file_exists or feedback_path.stat().st_size == 0:
                writer.writerow([
                    "Timestamp",
                    "Mode",
                    "Agent",
                    "Helpful",
                    "Correction Notes",
                    "Ideal Answer",
                ])

            writer.writerow([
                datetime.now().isoformat(timespec="seconds"),
                st.session_state.get("paai_mode", "Demo"),
                st.session_state.get("selected_agent", "Unknown"),
                st.session_state.paai_feedback_choice,
                feedback_notes,
                ideal_answer,
            ])

        try:
            log_activity(
                user_question="Feedback submitted",
                routed_agent=st.session_state.get("selected_agent", "Unknown"),
                action="Save feedback",
                result_summary=f"Helpful: {st.session_state.paai_feedback_choice}",
            )
        except Exception:
            pass

        st.success("Feedback saved.")
        st.session_state.paai_feedback_choice = ""


# --- PAAI USER GREETING V1 ---
from datetime import datetime as paai_datetime

def get_time_based_wish():
    current_hour = paai_datetime.now().hour

    if current_hour < 12:
        return "Good morning"
    elif current_hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


st.sidebar.divider()
st.sidebar.subheader("User")

if "paai_display_name" not in st.session_state:
    st.session_state.paai_display_name = ""

entered_display_name = st.sidebar.text_input(
    "What should PAAI call you?",
    value=st.session_state.paai_display_name,
    placeholder="Type your first name",
    key="paai_display_name_input",
)

if entered_display_name.strip():
    st.session_state.paai_display_name = entered_display_name.strip()

display_name = st.session_state.get("paai_display_name", "").strip()
current_mode = st.session_state.get("paai_mode", "Demo")
wish = get_time_based_wish()

if display_name:
    if current_mode == "Demo":
        st.sidebar.success(f"{wish}, {display_name} 👋 Welcome to PAAI Demo.")
    else:
        st.sidebar.success(f"{wish}, {display_name} 👋 Welcome back to PAAI 1.0.")
else:
    if current_mode == "Demo":
        st.sidebar.info(f"{wish} 👋 Welcome to PAAI Demo.")
    else:
        st.sidebar.info(f"{wish} 👋 Welcome back to PAAI 1.0.")
