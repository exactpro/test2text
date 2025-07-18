import io

import streamlit as st
import csv


def show():
    st.title("Upload a file with requirements.")

    uploaded_files = st.file_uploader("Choose a file with requirements", type="csv")

    for uploaded_file in uploaded_files:
        try:

            stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
            reader = csv.reader(stringio)
            rows = list(reader)
            # run indexing

            if rows:
                st.success("CSV file uploaded and parsed successfully!")
                st.subheader("Extracted Rows:")
                # Display as a table
                st.table(rows)
            else:
                st.warning("The uploaded CSV file is empty.")
        except Exception as e:
            st.error(f"Failed to parse CSV file: {e}")

    if not uploaded_files:
        st.info("Please upload a *.trace.csv file to extract rows.")
        return False
