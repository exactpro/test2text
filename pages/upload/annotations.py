
import streamlit as st

from services.loaders.convert_trace_annos import trace_test_cases_to_annos


def show():
    st.title("Upload *.trace.csv file")

    uploaded_files = st.file_uploader("Choose a *.trace.csv file", type="csv", accept_multiple_files=True)

    if not uploaded_files:
        st.info("Please upload a *.trace.csv file to extract rows.")
        return False

    st.success("CSV file uploaded and parsed successfully!")

    trace_test_cases_to_annos(uploaded_files)

    #index_annotations_from_files(uploaded_files)  #TODO
