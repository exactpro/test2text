
import streamlit as st

from test2text.services.loaders.convert_trace_annos import trace_test_cases_to_annos
from test2text.services.loaders.index_annotations import index_annotations_from_files


def show():
    with st.form("Upload *.trace.csv file"):
        st.header("Upload *.trace.csv file")

        st.subheader("1. Choose an action to execute")

        chosen_option = st.selectbox("Choose an action:", ("Write test cases and their annotations to database",
                                                                    "Index annotations"))
        st.subheader("2. Choose *.trace.csv files")
        uploaded_files = st.file_uploader("Choose files", type="csv", accept_multiple_files=True)

        if not uploaded_files:
            st.info("Please upload a *.trace.csv file to extract annotations.")
            submitted = st.form_submit_button("Start")
            return False

        st.success("CSV file uploaded successfully!")
        submitted = st.form_submit_button("Start")

    if submitted:
        st.subheader("Results:")
        if chosen_option == "Index annotations":
            from test2text.services.loaders.index_annotations import index_annotations_from_files
            index_annotations_from_files(uploaded_files)
        else:
            from test2text.services.loaders.convert_trace_annos import trace_test_cases_to_annos
            trace_test_cases_to_annos(uploaded_files)


if __name__ == "__main__":
    show()
