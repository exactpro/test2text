import streamlit as st

LOAD_TRACE_FILE = "Load from trace file"
LOAD_AND_CONCAT_TRACE_FILE = "Load and concatenate trace files"


def show_annotations():
    st.header("Upload *.trace.csv file")

    st.subheader("1. Choose an action to execute")
    chosen_option = st.selectbox(
        "Choose an action:", (LOAD_TRACE_FILE, LOAD_AND_CONCAT_TRACE_FILE)
    )
    if chosen_option == LOAD_TRACE_FILE:
        st.info(
            "All annotations will be loaded as is. Each line will represent an annotation occurrence."
        )
    elif chosen_option == LOAD_AND_CONCAT_TRACE_FILE:
        st.info(
            "Annotations will be grouped by test cases and concatenated, For each test case only 1 very detailed annotation will be created."
        )

    with st.form("upload_annotations_form"):
        st.subheader("2. Choose *.trace.csv files")
        uploaded_files = st.file_uploader(
            "Choose files", type="trace.csv", accept_multiple_files=True
        )

        if not uploaded_files:
            st.info("Please upload a *.trace.csv file to extract annotations.")

        submitted = st.form_submit_button("Start")

    if submitted:
        st.subheader("Results:")
        with st.spinner("Loading trace files...", show_time=True):
            if chosen_option == LOAD_TRACE_FILE:
                from test2text.services.loaders.index_annotations import (
                    index_annotations_from_files,
                )

                index_annotations_from_files(uploaded_files)

            elif chosen_option == LOAD_AND_CONCAT_TRACE_FILE:
                from test2text.services.loaders.convert_trace_annos import (
                    trace_test_cases_to_annos,
                )

                trace_test_cases_to_annos(uploaded_files)
            else:
                st.error("Unknown action selected. Please try again.")


if __name__ == "__main__":
    show_annotations()
