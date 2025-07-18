import streamlit as st

import pages.upload as upload


PAGES = {
    "Annotations Upload": upload.annotations.show,
    "Requirements Upload": upload.requirements.show,
}


def main():
    st.set_page_config(page_title="Test2Text App", layout="wide")
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    page = PAGES[selection]
    page()


if __name__ == "__main__":
    main()
