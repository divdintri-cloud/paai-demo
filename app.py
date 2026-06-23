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


def save_books_to_library(draft_df):
    BOOKS_DB_PATH.parent.mkdir(exist_ok=True)

    if BOOKS_DB_PATH.exists():
        existing_df = pd.read_csv(BOOKS_DB_PATH)
        combined_df = pd.concat([existing_df, draft_df], ignore_index=True)
    else:
        combined_df = draft_df.copy()

    if "Title" in combined_df.columns and "Author" in combined_df.columns:
        combined_df["Title"] = combined_df["Title"].fillna("").astype(str).str.strip()
        combined_df["Author"] = combined_df["Author"].fillna("").astype(str).str.strip()

        combined_df = combined_df.drop_duplicates(
            subset=["Title", "Author"],
            keep="first",
        )

    combined_df.to_csv(BOOKS_DB_PATH, index=False)
    return combined_df


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


def show_add_book_flow():
    st.header("Literacy Agent - Add Book")

    uploaded_book_photo = st.file_uploader(
        "Upload a clear photo of a book cover, book stack, or bookshelf section",
        type=["jpg", "jpeg", "png"],
        key="book_upload",
    )

    if uploaded_book_photo:
        st.image(uploaded_book_photo, caption="Uploaded book photo", use_container_width=True)

    if st.button("Analyze Book Photo"):
        if uploaded_book_photo is None:
            st.warning("Please upload a book photo first.")
            return

        with st.spinner("Reading book photo and preparing draft inventory..."):
            result = build_enriched_book_inventory([uploaded_book_photo])

        if isinstance(result, dict) and "error" in result:
            st.error(result["error"])
            st.text(result.get("raw_output", ""))
            return

        draft_df = pd.DataFrame(result.get("books", []))

        if draft_df.empty:
            st.warning("I could not detect any books from this photo. Try a clearer close-up photo.")
            return

        st.success(f"Detected {len(draft_df)} book(s). Review before saving.")

        display_columns = [
            col for col in [
                "Display Title",
                "Title",
                "Original Title",
                "Author",
                "Language",
                "Genre",
                "Extraction Confidence",
                "Needs Review",
                "Why Uncertain",
                "Thumbnail",
            ]
            if col in draft_df.columns
        ]

        st.dataframe(draft_df[display_columns], use_container_width=True)

        if st.button("Save Detected Book(s) to My Library"):
            saved_df = save_books_to_library(draft_df)
            st.success(f"Saved. Your library now has {len(saved_df)} unique book rows.")


def show_book_ownership(question):
    st.header("Literacy Agent - Book Search")

    book_query = clean_book_query(question)

    if not book_query:
        st.warning("Please include the book title or author.")
        return

    result = check_book_ownership(book_query)

    st.write(result["message"])

    matches = result.get("matches", [])

    if matches:
        for match in matches:
            col1, col2 = st.columns([1, 4])

            with col1:
                thumbnail = match.get("Thumbnail")
                if thumbnail:
                    st.image(thumbnail, width=90)
                else:
                    st.write("No cover")

            with col2:
                display_title = (
                    match.get("Display Title")
                    or match.get("Original Title")
                    or match.get("Title")
                    or "Untitled"
                )

                st.markdown(f"### {display_title}")
                st.write(f"**Author:** {match.get('Author', 'Unclear')}")
                st.write(f"**Language:** {match.get('Language', 'Unclear')}")
                st.write(f"**Genre:** {match.get('Genre', 'Unclear')}")
                st.caption(
                    f"Extraction confidence: {match.get('Extraction Confidence', 'Unclear')}"
                )


def show_book_recommendations(question):
    st.header("Literacy Agent - Mood-Based Recommendations")

    if not BOOKS_DB_PATH.exists():
        st.warning("I do not see a saved book inventory yet. Add books first by uploading book photos.")
        return

    df = pd.read_csv(BOOKS_DB_PATH)

    if df.empty:
        st.warning("Your saved book inventory is empty. Add books first.")
        return

    mood = extract_mood_from_question(question)

    st.write(f"Using mood: **{mood}**")

    with st.spinner("Finding 3 books from your saved library..."):
        recommendation_text = recommend_books_by_mood(
            mood=mood,
            books_context=df.to_string(index=False),
        )

    try:
        recommendation_json = json.loads(recommendation_text)
        recommendations = recommendation_json.get("recommendations", [])

        if not recommendations:
            st.info("No recommendations found.")
            return

        for book in recommendations[:3]:
            col1, col2 = st.columns([1, 4])

            thumbnail = book.get("thumbnail")

            with col1:
                if thumbnail:
                    st.image(thumbnail, width=110)
                else:
                    st.write("No cover")

            with col2:
                st.markdown(f"### {book.get('title', 'Untitled')}")
                st.write(f"**Author:** {book.get('author', 'Unclear')}")
                st.write(f"**Language:** {book.get('language', 'Unclear')}")
                st.write(f"**Subject:** {book.get('genre_or_subject', 'Unclear')}")
                st.write(f"**Why this fits:** {book.get('why_this_fits', '')}")
                st.caption(book.get("confidence_note", ""))

    except Exception as error:
        st.warning("The recommendation response was not in card format. Showing raw response.")
        st.write(recommendation_text)
        st.caption(f"Parsing error: {error}")


def load_saved_books():
    books_path = get_books_inventory_path()

    if not books_path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(books_path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()

    return df


def get_subject_dashboard(df):
    if df.empty:
        return pd.DataFrame(columns=["Subject", "Book Count"])

    if "Online Categories" in df.columns:
        subject_source = df["Online Categories"].fillna("").astype(str)
    elif "Genre" in df.columns:
        subject_source = df["Genre"].fillna("").astype(str)
    else:
        return pd.DataFrame(columns=["Subject", "Book Count"])

    subjects = []

    for value in subject_source:
        if not value.strip():
            subjects.append("Unclear")
        else:
            for subject in value.replace(";", ",").split(","):
                cleaned = subject.strip()
                if cleaned:
                    subjects.append(cleaned)

    if not subjects:
        subjects = ["Unclear"]

    subject_df = pd.Series(subjects).value_counts().reset_index()
    subject_df.columns = ["Subject", "Book Count"]

    return subject_df


def find_duplicate_books(df):
    if df.empty or "Title" not in df.columns or "Author" not in df.columns:
        return pd.DataFrame()

    check_df = df.copy()

    check_df["Title Clean"] = (
        check_df["Title"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    check_df["Author Clean"] = (
        check_df["Author"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    duplicates_df = check_df[
        check_df.duplicated(
            subset=["Title Clean", "Author Clean"],
            keep=False,
        )
    ].copy()

    return duplicates_df


def show_library_summary():
    st.header("Literacy Agent - Saved Library")

    df = load_saved_books()

    if df.empty:
        st.warning("No saved books found yet. Add books by uploading book photos.")
        return

    st.subheader("Library Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total books", len(df))

    with col2:
        if "Language" in df.columns:
            st.metric("Languages", df["Language"].fillna("Unclear").nunique())
        else:
            st.metric("Languages", "N/A")

    with col3:
        if "Author" in df.columns:
            st.metric("Authors", df["Author"].fillna("Unclear").nunique())
        else:
            st.metric("Authors", "N/A")

    if "Language" in df.columns:
        st.subheader("Books by Language")
        language_df = df["Language"].fillna("Unclear").replace("", "Unclear").value_counts().reset_index()
        language_df.columns = ["Language", "Book Count"]
        st.dataframe(language_df, use_container_width=True)

    st.subheader("Subject Dashboard")
    subject_df = get_subject_dashboard(df)

    if subject_df.empty:
        st.info("No subject information found yet.")
    else:
        st.dataframe(subject_df, use_container_width=True)

    st.subheader("Inventory Preview")

    display_columns = [
        col for col in [
            "Display Title",
            "Title",
            "Original Title",
            "Author",
            "Language",
            "Genre",
            "Mood Fit",
            "Extraction Confidence",
            "Thumbnail",
        ]
        if col in df.columns
    ]

    st.dataframe(df[display_columns], use_container_width=True)


def show_all_books():
    st.header("Literacy Agent - All Books")

    df = load_saved_books()

    if df.empty:
        st.warning("No saved books found yet.")
        return

    search_text = st.text_input("Search books", value="")

    filtered_df = df.copy()

    if search_text.strip():
        search = search_text.lower().strip()

        searchable = (
            filtered_df.get("Title", "").fillna("").astype(str)
            + " "
            + filtered_df.get("Display Title", "").fillna("").astype(str)
            + " "
            + filtered_df.get("Original Title", "").fillna("").astype(str)
            + " "
            + filtered_df.get("Author", "").fillna("").astype(str)
            + " "
            + filtered_df.get("Language", "").fillna("").astype(str)
            + " "
            + filtered_df.get("Genre", "").fillna("").astype(str)
        ).str.lower()

        filtered_df = filtered_df[searchable.str.contains(search, na=False)]

    st.write(f"Showing {len(filtered_df)} book(s).")

    display_columns = [
        col for col in [
            "Display Title",
            "Title",
            "Original Title",
            "Translated Title",
            "Author",
            "Language",
            "Script Detected",
            "Genre",
            "Mood Fit",
            "Energy Level",
            "Country or Region",
            "Award or Notability Note",
            "Extraction Confidence",
            "Needs Review",
            "Photo Number",
            "Thumbnail",
        ]
        if col in filtered_df.columns
    ]

    st.dataframe(filtered_df[display_columns], use_container_width=True)

    csv_data = filtered_df.to_csv(index=False)

    st.download_button(
        label="Download Books CSV",
        data=csv_data,
        file_name="books_inventory_export.csv",
        mime="text/csv",
    )


def show_subject_dashboard_only():
    st.header("Literacy Agent - Subject Dashboard")

    df = load_saved_books()

    if df.empty:
        st.warning("No saved books found yet.")
        return

    subject_df = get_subject_dashboard(df)

    if subject_df.empty:
        st.info("No subject information found yet.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total subjects", len(subject_df))

    with col2:
        st.metric("Largest subject", subject_df.iloc[0]["Subject"])

    with col3:
        st.metric("Books in largest subject", subject_df.iloc[0]["Book Count"])

    st.dataframe(subject_df, use_container_width=True)


def show_duplicate_check():
    st.header("Literacy Agent - Duplicate Check")

    df = load_saved_books()

    if df.empty:
        st.warning("No saved books found yet.")
        return

    duplicates_df = find_duplicate_books(df)

    if duplicates_df.empty:
        st.success("No duplicate books found based on Title + Author.")
        return

    st.warning(f"Found {len(duplicates_df)} duplicate book rows.")

    display_columns = [
        col for col in [
            "Title",
            "Display Title",
            "Original Title",
            "Author",
            "Language",
            "Genre",
            "Extraction Confidence",
            "Photo Number",
        ]
        if col in duplicates_df.columns
    ]

    st.dataframe(duplicates_df[display_columns], use_container_width=True)


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
            <div style="font-size: 28px; font-weight: 800; margin-bottom: 10px;">
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


def show_paai_home():
    st.header("PAAI Home")

    mode = st.session_state.get("paai_mode", "Demo")

    st.markdown(
        f"""
        <div style="font-size: 14px; color: #555; margin-bottom: 14px;">
            Mode: <b>{mode}</b>. Quick overview across available PAAI tools.
        </div>
        """,
        unsafe_allow_html=True,
    )

    books_df = load_saved_books()
    grocery_info = load_grocery_history_info()

    if mode == "Demo":
        col1, col2 = st.columns(2)
    else:
        col1, col2, col3 = st.columns(3)

    # Books tile values
    if books_df.empty:
        books_main = "0"
        books_detail_1 = "No saved books yet"
        books_detail_2 = "Upload a book photo in Literacy Agent"
    else:
        language_count = (
            books_df["Language"].fillna("Unclear").nunique()
            if "Language" in books_df.columns
            else "N/A"
        )
        duplicate_count = len(find_duplicate_books(books_df))
        books_main = f"{len(books_df)} books"
        books_detail_1 = f"{language_count} language(s)"
        books_detail_2 = f"{duplicate_count} duplicate row(s)"

    with col1:
        render_home_tile(
            title="Books",
            main_value=books_main,
            detail_1=books_detail_1,
            detail_2=books_detail_2,
            background_color="#eff6ff",
            border_color="#3b82f6",
        )

    # Grocery tile values
    if not grocery_info.get("has_history"):
        groceries_main = "No scan"
        groceries_detail_1 = "No grocery photo analyzed yet"
        groceries_detail_2 = "Upload a fridge or pantry photo"
        grocery_color = "#fff7ed"
        grocery_border = "#f97316"
    else:
        last_uploaded_at = grocery_info["last_uploaded_at"]
        latest_result = grocery_info["latest_result"]
        is_stale, age_days = is_grocery_analysis_stale(last_uploaded_at, stale_after_days=3)

        shopping_count = len(latest_result.get("shopping_list", []))
        manual_count = len(latest_result.get("manual_check", []))

        groceries_main = f"{shopping_count} suggestions"
        groceries_detail_1 = f"Last analyzed: {last_uploaded_at}"
        groceries_detail_2 = f"{manual_count} manual check(s)"

        if is_stale:
            grocery_color = "#fef2f2"
            grocery_border = "#ef4444"
        else:
            grocery_color = "#ecfdf5"
            grocery_border = "#10b981"

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
            payment_data = get_payment_summary()
            payment_summary = payment_data["summary"]

            render_home_tile(
                title="Payment Reminders",
                main_value=f"{payment_summary['due_soon_count']} due soon",
                detail_1=f"{payment_summary['overdue_count']} overdue",
                detail_2=f"${payment_summary['total_pending_amount']:,.2f} pending",
                background_color="#f5f3ff",
                border_color="#8b5cf6",
            )

    st.divider()

    st.subheader("Ask PAAI")

    if mode == "Demo":
        st.caption("Demo mode supports book and grocery questions. Payment and unfinished agents are hidden.")
        prompt_label = "Ask me about books or grocery list"
    else:
        prompt_label = "Ask me about books, payment reminders, or grocery list"

    home_question = st.text_input(
        prompt_label,
        value="",
        key="home_paai_question",
    )

    if st.button("Ask PAAI from Home"):
        if mode == "Demo" and is_payment_question(home_question):
            st.info("Payment Reminder Agent is disabled in Demo mode.")
        else:
            route_home_question(home_question)


    st.divider()

    st.subheader("Recent Log Updates")

    recent_df = get_recent_activity(limit=5)

    if recent_df.empty:
        st.info("No recent PAAI activity yet.")
    else:
        st.dataframe(recent_df, use_container_width=True)


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
    st.header("Literacy Agent")

    literacy_options = [
        "View my saved library",
        "List all books",
        "Subject dashboard",
        "Duplicate check",
        "Add book from photo",
        "Check if I own a book",
        "Recommend books by mood",
    ]

    default_literacy_action = st.session_state.get("literacy_action", "View my saved library")

    if default_literacy_action not in literacy_options:
        default_literacy_action = "View my saved library"

    literacy_action = st.selectbox(
        "What do you want to do?",
        literacy_options,
        index=literacy_options.index(default_literacy_action),
    )

    st.session_state.literacy_action = literacy_action

    if literacy_action == "View my saved library":
        show_library_summary()

    elif literacy_action == "List all books":
        show_all_books()

    elif literacy_action == "Subject dashboard":
        show_subject_dashboard_only()

    elif literacy_action == "Duplicate check":
        show_duplicate_check()

    elif literacy_action == "Add book from photo":
        show_add_book_flow()

    elif literacy_action == "Check if I own a book":
        book_question = st.text_input("Book question", value=st.session_state.get("routed_question", "Do I own Lean In?"))
        if st.button("Check Library"):
            show_book_ownership(book_question)

    elif literacy_action == "Recommend books by mood":
        recommendation_question = st.text_input(
            "Mood recommendation question",
            value=st.session_state.get("routed_question", "Recommend a book for an empowered mood"),
        )
        if st.button("Recommend Books"):
            show_book_recommendations(recommendation_question)

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
