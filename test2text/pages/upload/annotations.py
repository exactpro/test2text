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
        with st.spinner("Loading trace files...", show_time=True):
            if chosen_option == LOAD_TRACE_FILE:
                from test2text.services.loaders.index_annotations import (
                    index_annotations_from_files,
                )

                st.subheader("Processing files:")
                file_order, file_name, proc_file = st.columns(3)
                with file_order:
                    st.write("Number")
                with file_name:
                    st.write("File name")
                with proc_file:
                    st.write("Detected annotations")

                def on_file_start(file_number: str, file_name: str):
                    file_order_column, file_name_column, proc_file_column = st.columns(
                        3
                    )
                    with file_order_column:
                        st.write(file_number)
                    with file_name_column:
                        st.write(file_name)
                    with proc_file_column:
                        file_counter = st.empty()
                    return file_counter

                index_annotations_from_files(
                    uploaded_files, on_file_start=on_file_start
                )
                st.success("Annotations loaded successfully!")

            elif chosen_option == LOAD_AND_CONCAT_TRACE_FILE:
                from test2text.services.loaders.convert_trace_annos import (
                    trace_test_cases_to_annos,
                )

                trace_test_cases_to_annos(uploaded_files)
                st.success("Annotations loaded and concatenated successfully!")
            else:
                st.error("Unknown action selected. Please try again.")


if __name__ == "__main__":
    show_annotations()
