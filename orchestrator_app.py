import streamlit as st

from skills.grocery_skills import extract_grocery_items_from_photo
from skills.literacy_skills import check_book_ownership
from skills.payment_skills import ask_payment_agent, get_payment_summary


st.set_page_config(page_title="PAAI - Orchestrator Agent", layout="wide")

st.title("PAAI - Chief of Staff Orchestrator Agent")

st.write(
    "Ask PAAI one question. The Orchestrator will route it to the right specialist agent."
)

st.markdown(
    """
Examples:
- Do I own Lean In?
- What payments are due soon?
- Are any subscriptions coming up?
- What groceries do I have?
"""
)

question = st.text_input(
    "Ask PAAI",
    value="What payments are due soon?",
)

uploaded_grocery_photo = st.file_uploader(
    "Optional: upload a grocery, fridge, or pantry photo",
    type=["jpg", "jpeg", "png"],
)

if st.button("Ask Orchestrator"):
    lower_question = question.lower()

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
        "renewals",
        "paid",
        "amount",
        "reminder",
        "credit card",
        "mortgage",
        "insurance",
    ]

    book_keywords = [
        "do i own",
        "do we own",
        "book",
        "books",
        "library",
        "author",
        "read",
    ]

    grocery_keywords = [
        "grocery",
        "groceries",
        "fridge",
        "pantry",
        "food",
        "shopping",
        "restock",
        "doordash",
        "door dash",
        "instacart",
    ]

    if uploaded_grocery_photo is not None or any(keyword in lower_question for keyword in grocery_keywords):
        st.subheader("Routed to: Grocery Photo Agent")

        if uploaded_grocery_photo is None:
            st.warning("Please upload a grocery, fridge, or pantry photo.")
        else:
            with st.spinner("Reading grocery photo..."):
                result = extract_grocery_items_from_photo(uploaded_grocery_photo)

            st.write(result.get("summary", ""))

            items = result.get("items", [])

            if items:
                st.dataframe(items, use_container_width=True)
            else:
                st.info("No grocery items were extracted.")

            suggestions = result.get("shopping_suggestions", [])

            if suggestions:
                st.subheader("Shopping Suggestions")
                for suggestion in suggestions:
                    st.write(f"- {suggestion}")

    elif any(keyword in lower_question for keyword in payment_keywords):
        st.subheader("Routed to: Payment Reminder Agent")

        payment_data = get_payment_summary()
        summary = payment_data["summary"]
        due_soon_df = payment_data["due_soon"]
        overdue_df = payment_data["overdue"]
        subscriptions_df = payment_data["subscriptions"]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total payments", summary["total_payments"])

        with col2:
            st.metric("Due soon", summary["due_soon_count"])

        with col3:
            st.metric("Overdue", summary["overdue_count"])

        with col4:
            st.metric("Pending amount", f"${summary['total_pending_amount']:,.2f}")

        with st.spinner("Asking Payment Reminder Agent..."):
            answer = ask_payment_agent(question)

        st.write(answer)

        with st.expander("Show due soon payments"):
            if due_soon_df.empty:
                st.info("No unpaid payments due soon.")
            else:
                st.dataframe(due_soon_df, use_container_width=True)

        with st.expander("Show overdue payments"):
            if overdue_df.empty:
                st.success("No overdue unpaid payments.")
            else:
                st.dataframe(overdue_df, use_container_width=True)

        with st.expander("Show subscriptions"):
            if subscriptions_df.empty:
                st.info("No subscriptions found.")
            else:
                st.dataframe(subscriptions_df, use_container_width=True)

    elif any(keyword in lower_question for keyword in book_keywords):
        st.subheader("Routed to: Literacy Agent")

        cleaned_query = (
            question
            .replace("Do I own", "")
            .replace("do I own", "")
            .replace("do i own", "")
            .replace("Do we own", "")
            .replace("do we own", "")
            .replace("?", "")
            .strip()
        )

        result = check_book_ownership(cleaned_query)

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

    else:
        st.info(
            "I do not know which specialist agent should handle this yet. "
            "Try asking about books, payments, subscriptions, bills, groceries, fridge, or pantry."
        )
