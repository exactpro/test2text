from pathlib import Path

import streamlit as st





def main():

    st.set_page_config(page_title="Test2Text App", layout="wide")
    st.header("Test2Text")
    st.markdown("By this application you can:")
    st.markdown("- Upload annotations and requirements to create embeddings from text;")
    st.markdown("- Save texts to database;")
    st.markdown("- Create report about the coverage of the requirements by the test cases.")



if __name__ == "__main__":
    main()
