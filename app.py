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
from skills.payment_skills import ask_payment_agent, get_payment_summary
from skills.activity_log import log_activity, get_recent_activity


# BOOKS_DB_PATH removed for Demo Mode; use get_books_inventory_path() instead

st.set_page_config(page_title="PAAI - Personal AI Assistant", layout="wide")

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
    "Grocery Help Agent",
    "Activity Log",
]

personal_agent_options = [
    "PAAI Home",
    "Literacy Agent",
    "Payment Reminder Agent",
    "Grocery Help Agent",
    "Activity Log",
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



def render_home_tile(title, main_value, detail_1, detail_2, background_color, border_color):
    title = display_value(title)
    main_value = display_value(main_value)
    detail_1 = display_value(detail_1)
    detail_2 = display_value(detail_2)

    st.markdown(
        f"""
        <div style="
            background-color: {background_color};
            border-left: 6px solid {border_color};
            padding: 16px;
            border-radius: 14px;
            min-height: 170px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        ">
            <div style="font-size: 15px; font-weight: 700; margin-bottom: 8px;">
                {title}
            </div>
            <div style="font-size: 24px; font-weight: 800; margin-bottom: 10px;">
                {main_value}
            </div>
            <div style="font-size: 13px; line-height: 1.5;">
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

    if st.session_state.get("paai_mode", "Demo") == "Demo" and is_payment_question(home_question):
        st.info("Payment Reminder Agent is disabled in Demo mode.")
        return

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

def show_paai_home():
    st.header("PAAI Home")

    mode = st.session_state.get("paai_mode", "Demo")

    if mode == "Demo":
        st.warning(
            "Demo Mode: safe sharing version. Book and grocery uploads may be processed by AI. "
            "Please do not upload sensitive images, IDs, private documents, payment screenshots, or personal records."
        )

    st.markdown(
        f"""
        <div style="font-size: 13px; color: #555; margin-bottom: 14px;">
            Mode: <b>{mode}</b>. Quick overview across available PAAI tools.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Books tile - use the same library file as Literacy Agent
    try:
        books_df = load_saved_books()
        st.caption(f"DEBUG Home books path: {get_books_inventory_path()} · rows: {len(books_df)}")
    except Exception as error:
        st.caption(f"DEBUG Home books error: {error}")
        books_df = pd.DataFrame()

    if books_df is None:
        books_df = pd.DataFrame()

    if books_df.empty:
        books_main = "Data not available"
        books_detail_1 = "No saved books found"
        books_detail_2 = f"Library file: {get_books_inventory_path()}"
    else:
        books_main = f"{len(books_df)} books saved"

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

    # Grocery tile
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
        else:
            groceries_main = f"{shopping_count} suggestions"
            groceries_detail_1 = f"Last analyzed: {grocery_info.get('last_uploaded_at', 'Data not available')}"
            groceries_detail_2 = f"{manual_count} manual check(s)"

        grocery_color = "#ecfdf5"
        grocery_border = "#10b981"

    if mode == "Demo":
        col1, col2 = st.columns(2)
    else:
        col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Books")
        st.metric("Saved books", len(books_df))
        st.caption(books_detail_1)
        st.caption(books_detail_2)

    with col2:
        render_home_tile(
            title="Groceries",
            main_value=groceries_main,
            detail_1=groceries_detail_1,
            detail_2=groceries_detail_2,
            background_color=grocery_color,
            border_color=grocery_border,
        )

    if mode != "Demo":
        with col3:
            try:
                payment_data = get_payment_summary()
                payment_summary = payment_data["summary"]
                payment_main = f"{payment_summary['due_soon_count']} due soon"
                payment_detail_1 = f"{payment_summary['overdue_count']} overdue"
                payment_detail_2 = f"${payment_summary['total_pending_amount']:,.2f} pending"
            except Exception:
                payment_main = "Data not available"
                payment_detail_1 = "No payment summary available"
                payment_detail_2 = "Add payment reminders to generate summary"

            render_home_tile(
                title="Payment Reminders",
                main_value=payment_main,
                detail_1=payment_detail_1,
                detail_2=payment_detail_2,
                background_color="#f5f3ff",
                border_color="#8b5cf6",
            )

    st.divider()

    st.subheader("Ask PAAI")

    prompt_label = (
        "Ask me about books or grocery list"
        if mode == "Demo"
        else "Ask me about books, payment reminders, or grocery list"
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



if agent == "PAAI Home":
    show_paai_home()


elif agent == "Grocery Help Agent":
    show_grocery_agent()

elif agent == "Payment Reminder Agent":
    routed_question = st.session_state.get("routed_question", "")
    if routed_question:
        st.caption(f"Routed question: {routed_question}")
        show_payment_agent(routed_question)
    else:
        show_payment_agent()

elif agent == "Literacy Agent":
    show_literacy_agent_tabs()


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
