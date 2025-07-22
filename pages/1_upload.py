from pathlib import Path

import streamlit as st

import pages.upload as upload

PAGES = {
    "Annotations Upload": upload.annotations.show,
    "Requirements Upload": upload.requirements.show,
}

st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]
page()
