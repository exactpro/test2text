import streamlit as st
import csv

st.title("Upload *.trace.csv file")

uploaded_file = st.file_uploader("Choose a *.trace.csv file", type="csv")

if uploaded_file is not None:
    try:
        # Read the file as a string
        with open(uploaded_file, "r") as trace_file:
            reader = csv.reader(trace_file)
            rows = list(reader)
            # run indexing
            # run trace

        if rows:
            st.success("CSV file uploaded and parsed successfully!")
            st.subheader("Extracted Rows:")
            # Display as a table
            st.table(rows)
        else:
            st.warning("The uploaded CSV file is empty.")
    except Exception as e:
        st.error(f"Failed to parse CSV file: {e}")
else:
    st.info("Please upload a *.trace.csv file to extract rows.")