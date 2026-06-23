from pathlib import Path

import pandas as pd
import streamlit as st

from skills.literacy_skills import (
    build_enriched_book_inventory,
    recommend_books_by_mood,
    check_book_ownership,
)
from skills.payment_skills import get_payment_summary, ask_payment_agent
from skills.grocery_skills import (
    extract_grocery_items_from_photo,
    save_grocery_analysis,
    load_grocery_history_info,
    is_grocery_analysis_stale,
)

from skills.literacy_skills import check_book_ownership

BOOKS_DB_PATH = Path("data/books_inventory.csv")


st.set_page_config(page_title="PAAI - Personal AI Assistant", layout="wide")

st.title("PAAI - Personal AI Assistant")
st.write(
    "PAAI helps with personal AI workflows like books, payments, grocery help, travel, planning, and AI PM transition."
)

agent = st.sidebar.selectbox(
    "Choose an agent",
    [
        "Chief of Staff Orchestrator Agent",
        "Literacy Agent",
        "Payment Reminder Agent",
        "Grocery Help Agent",
        "Entertainment Agent",
        "AI Product Manager Role Transition Agent",
        "Task & Planning Agent",
        "Travel Agent",
    ],
)

if "draft_books" not in st.session_state:
    st.session_state.draft_books = None

if "saved_books" not in st.session_state:
    st.session_state.saved_books = None

if "suggested_moods" not in st.session_state:
    st.session_state.suggested_moods = []

if "uploaded_file_names" not in st.session_state:
    st.session_state.uploaded_file_names = []

if "collection_summary" not in st.session_state:
    st.session_state.collection_summary = ""


def load_saved_library():
    if not BOOKS_DB_PATH.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(BOOKS_DB_PATH)
    except Exception:
        return pd.DataFrame()


def save_books_to_library(draft_df):
    BOOKS_DB_PATH.parent.mkdir(exist_ok=True)

    existing_df = load_saved_library()

    if existing_df.empty:
        combined_df = draft_df.copy()
    else:
        combined_df = pd.concat([existing_df, draft_df], ignore_index=True)

    if "Title" in combined_df.columns and "Author" in combined_df.columns:
        combined_df["Title"] = combined_df["Title"].fillna("").astype(str).str.strip()
        combined_df["Author"] = combined_df["Author"].fillna("").astype(str).str.strip()
        combined_df = combined_df.drop_duplicates(
            subset=["Title", "Author"],
            keep="first",
        )

    combined_df.to_csv(BOOKS_DB_PATH, index=False)
    return combined_df


def find_duplicate_books(df):
    if df.empty:
        return pd.DataFrame()

    required_columns = ["Title", "Author"]

    for column in required_columns:
        if column not in df.columns:
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


def show_duplicate_check(df):
    st.subheader("Duplicate Check")

    duplicates_df = find_duplicate_books(df)

    if duplicates_df.empty:
        st.success("No duplicate books found based on Title + Author.")
        return

    st.warning(f"Found {len(duplicates_df)} duplicate book rows.")

    display_columns = [
        col for col in [
            "Title",
            "Author",
            "Genre",
            "Language",
            "Extraction Confidence",
            "Photo Number",
        ]
        if col in duplicates_df.columns
    ]

    st.dataframe(
        duplicates_df[display_columns],
        use_container_width=True,
    )

    if st.button("Merge Duplicate Details and Save Clean Inventory"):
        merged_df, merged_duplicates_df = merge_duplicate_books(df)
        save_merged_book_inventory(merged_df)

        st.success(
            f"Duplicates merged. Inventory now has {len(merged_df)} unique book rows."
        )

        st.session_state.saved_books = merged_df

        with st.expander("Show merged duplicate source rows"):
            if merged_duplicates_df.empty:
                st.info("No duplicate source rows found.")
            else:
                st.dataframe(merged_duplicates_df, use_container_width=True)


def choose_better_value(values, prefer_longest=False):
    clean_values = []

    for value in values:
        if pd.isna(value):
            continue

        text_value = str(value).strip()

        if text_value and text_value.lower() not in ["nan", "none", "unclear", "unknown"]:
            clean_values.append(text_value)

    if not clean_values:
        return ""

    if prefer_longest:
        return max(clean_values, key=len)

    return clean_values[0]


def choose_best_confidence(values):
    ranking = {
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    best_value = ""
    best_score = 0

    for value in values:
        text_value = str(value).strip()
        score = ranking.get(text_value.lower(), 0)

        if score > best_score:
            best_value = text_value
            best_score = score

    return best_value


def merge_duplicate_books(df):
    if df.empty or "Title" not in df.columns or "Author" not in df.columns:
        return df, pd.DataFrame()

    work_df = df.copy()

    work_df["Title Clean"] = (
        work_df["Title"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    work_df["Author Clean"] = (
        work_df["Author"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    merged_rows = []
    duplicate_groups = []

    for _, group in work_df.groupby(["Title Clean", "Author Clean"], dropna=False):
        if len(group) == 1:
            row = group.iloc[0].drop(labels=["Title Clean", "Author Clean"]).to_dict()
            merged_rows.append(row)
            continue

        duplicate_groups.append(group.drop(columns=["Title Clean", "Author Clean"]))

        merged_row = {}

        for column in group.columns:
            if column in ["Title Clean", "Author Clean"]:
                continue

            values = group[column].tolist()

            if column == "Extraction Confidence":
                merged_row[column] = choose_best_confidence(values)

            elif column in ["Online Description", "Notes", "Why Uncertain"]:
                merged_row[column] = choose_better_value(values, prefer_longest=True)

            elif column in ["Photo Number"]:
                photo_values = sorted(
                    set(
                        str(value).strip()
                        for value in values
                        if not pd.isna(value) and str(value).strip()
                    )
                )
                merged_row[column] = ", ".join(photo_values)

            elif column in ["Needs Review"]:
                lowered = [str(value).lower().strip() for value in values]
                merged_row[column] = "Yes" if "yes" in lowered else "No"

            else:
                merged_row[column] = choose_better_value(values)

        merged_rows.append(merged_row)

    merged_df = pd.DataFrame(merged_rows)

    if duplicate_groups:
        duplicates_df = pd.concat(duplicate_groups, ignore_index=True)
    else:
        duplicates_df = pd.DataFrame()

    return merged_df, duplicates_df


def save_merged_book_inventory(merged_df):
    BOOKS_DB_PATH.parent.mkdir(exist_ok=True)
    merged_df.to_csv(BOOKS_DB_PATH, index=False)
    return merged_df


def show_minimal_library_view(df):
    st.subheader("My Library Summary")
    st.write(f"Total books: {len(df)}")


    if "Award or Notability Note" in df.columns:
        notable_df = df[
            ~df["Award or Notability Note"]
            .fillna("")
            .str.lower()
            .isin(["", "unknown", "notability unclear", "award information not found"])
        ]

        st.subheader("Notable Books")
        if len(notable_df) > 0:
            display_columns = [
                col for col in [
                    "Title",
                    "Author",
                    "Award or Notability Note",
                    "Genre",
                    "Mood Fit",
                ]
                if col in notable_df.columns
            ]
            st.dataframe(notable_df[display_columns], use_container_width=True)
        else:
            st.info("No notable books identified yet.")


def show_optional_details(df):
    with st.expander("Show full book inventory"):
        st.dataframe(df, use_container_width=True)

    with st.expander("Show books grouped by genre"):
        if "Genre" in df.columns:
            clean_df = df.copy()
            clean_df["Genre"] = clean_df["Genre"].fillna("Unclear").replace("", "Unclear")

            for genre, group_df in clean_df.groupby("Genre"):
                st.markdown(f"### {genre}")
                display_columns = [
                    col for col in ["Title", "Author", "Mood Fit", "Energy Level"]
                    if col in clean_df.columns
                ]
                st.dataframe(group_df[display_columns], use_container_width=True)

    with st.expander("Show books grouped by author"):
        if "Author" in df.columns:
            clean_df = df.copy()
            clean_df["Author"] = clean_df["Author"].fillna("Unclear").replace("", "Unclear")

            for author, group_df in clean_df.groupby("Author"):
                st.markdown(f"### {author}")
                display_columns = [
                    col for col in ["Title", "Genre", "Mood Fit", "Energy Level"]
                    if col in clean_df.columns
                ]
                st.dataframe(group_df[display_columns], use_container_width=True)

    with st.expander("Show language grouping"):
        if "Language" in df.columns:
            language_counts = df["Language"].fillna("Unclear").replace("", "Unclear").value_counts()
            language_df = language_counts.reset_index()
            language_df.columns = ["Language", "Count"]
            st.dataframe(language_df, use_container_width=True)

    with st.expander("Show country / region grouping"):
        if "Country or Region" in df.columns:
            country_counts = df["Country or Region"].fillna("Unclear").replace("", "Unclear").value_counts()
            country_df = country_counts.reset_index()
            country_df.columns = ["Country or Region", "Count"]
            st.dataframe(country_df, use_container_width=True)

    with st.expander("Show raw online metadata"):
        metadata_columns = [
            col for col in [
                "Title",
                "Author",
                "Metadata Source",
                "Online Categories",
                "Online Description",
                "Preview Link",
            ]
            if col in df.columns
        ]

        if metadata_columns:
            st.dataframe(df[metadata_columns], use_container_width=True)
        else:
            st.info("No online metadata columns found.")


def show_mood_recommendation(df, suggested_moods):
    import json

    st.subheader("Mood-Based Reading Recommendation")

    if suggested_moods:
        selected_mood = st.selectbox(
            "Pick a mood suggested from your library",
            suggested_moods,
        )
    else:
        selected_mood = st.text_input("Enter a mood", value="Reflective")

    if st.button("Recommend 3 Books for This Mood"):
        with st.spinner("Finding 3 books from your saved library..."):
            recommendation_text = recommend_books_by_mood(
                mood=selected_mood,
                books_context=df.to_string(index=False),
            )

        try:
            recommendation_json = json.loads(recommendation_text)
            recommendations = recommendation_json.get("recommendations", [])

            if not recommendations:
                st.info("No recommendations found.")
                return

            st.subheader("Recommended Books")

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

if agent == "Chief of Staff Orchestrator Agent":
    st.header("Chief of Staff Orchestrator Agent")

    st.write(
        "Ask PAAI a question. For now, the orchestrator can route book ownership questions to the Literacy Agent."
    )

    user_question = st.text_input(
        "Ask something",
        value="Do I own Lean In?",
    )

    if st.button("Ask Orchestrator"):
        lower_question = user_question.lower()

        book_keywords = [
            "do i own",
            "do we own",
            "is this book in my library",
            "is this in my library",
            "book",
            "library",
        ]

        if any(keyword in lower_question for keyword in book_keywords):
            cleaned_query = (
                user_question
                .replace("Do I own", "")
                .replace("do I own", "")
                .replace("do i own", "")
                .replace("?", "")
                .strip()
            )

            result = check_book_ownership(cleaned_query)

            st.write(result["message"])

            if result["matches"]:
                for match in result["matches"]:
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
        else:
            st.info(
                "I am not routing this question yet. Next, we can connect payments, tasks, travel, and groceries."
            )

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


def show_grocery_agent_ui(default_question="What groceries do I have?"):
    st.header("Grocery Help Agent")

    st.write(
        "Upload a fridge, pantry, grocery, or receipt photo. "
        "PAAI will identify visible items, running-low items, shopping suggestions, and manual checks."
    )

    st.info(f"Routed question: {default_question}")

    uploaded_grocery_photo = st.file_uploader(
        "Upload grocery/fridge/pantry image",
        type=["jpg", "jpeg", "png"],
        key="orchestrator_grocery_upload",
    )

    if uploaded_grocery_photo:
        st.image(
            uploaded_grocery_photo,
            caption="Uploaded grocery photo",
            use_container_width=True,
        )

    if st.button("Analyze Groceries", key="orchestrator_analyze_groceries"):
        if uploaded_grocery_photo is None:
            st.warning("Please upload a grocery, fridge, pantry, or receipt photo first.")
        else:
            with st.spinner("Analyzing grocery photo..."):
                result = extract_grocery_items_from_photo(uploaded_grocery_photo)

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

                st.text_area(
                    "Shopping list message",
                    value=shopping_message,
                    height=220,
                )

                st.download_button(
                    label="Download Shopping List",
                    data=shopping_message,
                    file_name="shopping_list.txt",
                    mime="text/plain",
                )


if agent == "Chief of Staff Orchestrator Agent":
    st.header("Chief of Staff Orchestrator Agent")

    user_question = st.text_input(
        "Ask PAAI",
        value="What groceries do I need to restock?",
    )

    if is_grocery_question(user_question):
        st.success("Routing this to Grocery Help Agent.")
        show_grocery_agent_ui(user_question)
    else:
        st.info(
            "This question is not routed yet. Grocery questions will route to Grocery Help Agent."
        )

elif agent == "Literacy Agent":
    st.header("Literacy Agent")

    tab1, tab2 = st.tabs(["My Saved Library", "Upload New Book Photos"])

    with tab1:
        st.subheader("My Saved Library")

        if st.button("Load My Saved Library"):
            st.session_state.saved_books = load_saved_library()

        saved_df = st.session_state.saved_books

        if saved_df is None:
            st.info("Click 'Load My Saved Library' to view books saved in data/books_inventory.csv.")
        elif saved_df.empty:
            st.warning("No saved books found yet. Upload photos and save a draft inventory first.")
        else:
            show_minimal_library_view(saved_df)
            show_duplicate_check(saved_df)
            show_mood_recommendation(saved_df, st.session_state.suggested_moods)
            show_optional_details(saved_df)

            csv_data = saved_df.to_csv(index=False)
            st.download_button(
                label="Download My Saved Library CSV",
                data=csv_data,
                file_name="books_inventory.csv",
                mime="text/csv",
            )

    with tab2:
        st.subheader("Upload New Book Photos")

        uploaded_files = st.file_uploader(
            "Upload photos of your bookshelves or book stacks",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            with st.expander("Show photos used for inventory extraction"):
                st.write(f"Photos uploaded: {len(uploaded_files)}")

                cols = st.columns(3)

                for index, uploaded_file in enumerate(uploaded_files):
                    with cols[index % 3]:
                        st.image(
                            uploaded_file,
                            caption=f"Photo {index + 1}: {uploaded_file.name}",
                            use_container_width=True,
                        )

            st.info(
                "Tip: for best extraction, upload close-up shelf sections. "
                "A good target is 8 to 15 books per photo."
            )

        if st.button("Build Draft Inventory"):
            if not uploaded_files:
                st.warning("Please upload at least one book photo.")
            else:
                st.session_state.uploaded_file_names = [file.name for file in uploaded_files]

                with st.spinner("Reading books, enriching metadata, and preparing draft inventory..."):
                    result = build_enriched_book_inventory(uploaded_files)

                if isinstance(result, dict) and "error" in result:
                    st.error(result["error"])
                    st.text(result["raw_output"])
                else:
                    st.session_state.draft_books = pd.DataFrame(result["books"])
                    st.session_state.suggested_moods = result["moods"].get("suggested_moods", [])
                    st.session_state.collection_summary = result.get("collection_summary", "")

                    st.success("Draft inventory created. Review it before saving.")

        if st.session_state.draft_books is not None:
            draft_df = st.session_state.draft_books

            st.subheader("Draft Inventory Review")
            st.write(f"Books detected: {len(draft_df)}")

            if st.session_state.collection_summary:
                st.write(st.session_state.collection_summary)

            st.dataframe(draft_df, use_container_width=True)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Save to My Library"):
                    saved_df = save_books_to_library(draft_df)
                    st.session_state.saved_books = saved_df
                    st.success(f"Saved. Your library now has {len(saved_df)} unique books.")

            with col2:
                if st.button("Clear Draft"):
                    st.session_state.draft_books = None
                    st.success("Draft cleared.")

            csv_data = draft_df.to_csv(index=False)
            st.download_button(
                label="Download Draft Inventory CSV",
                data=csv_data,
                file_name="draft_books_inventory.csv",
                mime="text/csv",
            )

elif agent == "Payment Reminder Agent":
    st.header("Payment Reminder Agent")

    payment_data = get_payment_summary()

    summary = payment_data["summary"]
    full_df = payment_data["dataframe"]
    overdue_df = payment_data["overdue"]
    due_soon_df = payment_data["due_soon"]
    subscriptions_df = payment_data["subscriptions"]

    st.subheader("Payment Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total payments", summary["total_payments"])

    with col2:
        st.metric("Due soon", summary["due_soon_count"])

    with col3:
        st.metric("Overdue", summary["overdue_count"])

    with col4:
        st.metric("Pending amount", f"${summary['total_pending_amount']:,.2f}")

    st.subheader("Due Soon")

    if due_soon_df.empty:
        st.info("No unpaid payments due in the next 7 days.")
    else:
        st.dataframe(due_soon_df, use_container_width=True)

    st.subheader("Overdue")

    if overdue_df.empty:
        st.success("No overdue unpaid payments.")
    else:
        st.warning("You have overdue unpaid payments. Please verify manually before taking action.")
        st.dataframe(overdue_df, use_container_width=True)

    with st.expander("Show subscriptions"):
        if subscriptions_df.empty:
            st.info("No subscriptions found.")
        else:
            st.dataframe(subscriptions_df, use_container_width=True)

    with st.expander("Show all payment reminders"):
        st.dataframe(full_df, use_container_width=True)

    st.subheader("Ask Payment Reminder Agent")

    payment_question = st.text_input(
        "Ask a payment question",
        value="What payments are due soon?",
    )

    if st.button("Ask Payment Agent"):
        with st.spinner("Checking your payment reminders..."):
            answer = ask_payment_agent(payment_question)

        st.write(answer)

elif agent == "Grocery Help Agent":
    st.header("Grocery Help Agent")

    st.write(
        "Upload a fridge, pantry, grocery, or receipt photo. "
        "PAAI will identify visible items, running-low items, shopping suggestions, and manual checks."
    )

    uploaded_grocery_photo = st.file_uploader(
        "Upload grocery/fridge/pantry image",
        type=["jpg", "jpeg", "png"],
    )

    if uploaded_grocery_photo:
        st.image(
            uploaded_grocery_photo,
            caption="Uploaded grocery photo",
            use_container_width=True,
        )

    if st.button("Analyze Groceries"):
        if uploaded_grocery_photo is None:
            st.warning("Please upload a grocery, fridge, pantry, or receipt photo first.")
        else:
            with st.spinner("Analyzing grocery photo..."):
                result = extract_grocery_items_from_photo(uploaded_grocery_photo)

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

                st.text_area(
                    "Shopping list message",
                    value=shopping_message,
                    height=220,
                )

                st.download_button(
                    label="Download Shopping List",
                    data=shopping_message,
                    file_name="shopping_list.txt",
                    mime="text/plain",
                )

else:
    st.header(agent)
    st.info("This agent will be added later.")
