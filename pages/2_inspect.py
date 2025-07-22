import streamlit as st

from report import make_a_report


PAGES = {
    "Make coverage report": make_a_report,
    #"Visualize vectors": ,
}

st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]
page()
