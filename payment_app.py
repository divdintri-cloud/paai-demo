import streamlit as st

from skills.payment_skills import (
    ask_payment_agent,
    get_payment_summary,
    parse_uploaded_payment_file,
    save_payment_reminders,
)


st.set_page_config(page_title="PAAI - Payment Reminder Agent", layout="wide")

st.title("PAAI - Payment Reminder Agent")
st.write("Track due soon, overdue, subscriptions, and import payment reminders from Excel, CSV, or Word.")

tab1, tab2 = st.tabs(["Payment Dashboard", "Import Payment File"])

with tab1:
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

with tab2:
    st.subheader("Import Payment File")

    st.warning(
        "Use a cleaned file. Avoid uploading bank account numbers, card numbers, transaction IDs, "
        "full addresses, or highly sensitive personal notes."
    )

    uploaded_file = st.file_uploader(
        "Upload payment reminders as Excel, CSV, or Word document",
        type=["xlsx", "xls", "csv", "docx"],
    )

    if "draft_payment_import" not in st.session_state:
        st.session_state.draft_payment_import = None

    if uploaded_file:
        st.write(f"Uploaded file: {uploaded_file.name}")

        if st.button("Preview Payment Reminders"):
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
            if st.button("Save Draft to Payment Reminders"):
                saved_df = save_payment_reminders(draft_df)
                st.success(f"Saved. You now have {len(saved_df)} payment reminder rows.")

        with col2:
            if st.button("Clear Draft Import"):
                st.session_state.draft_payment_import = None
                st.success("Draft import cleared.")

        csv_data = draft_df.to_csv(index=False)
        st.download_button(
            label="Download Draft Import CSV",
            data=csv_data,
            file_name="draft_payment_reminders.csv",
            mime="text/csv",
        )
