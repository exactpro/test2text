
import streamlit as st


def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"]::before {
                content: "📑 Test2Text";
                margin-left: 20px;
                margin-top: 20px;
                font-size: 30px;
                position: relative;
                top: 0px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    st.set_page_config(page_title="📑 Test2Text App", layout="wide", initial_sidebar_state="auto")
    add_logo()

    annotations = st.Page("pages/upload/annotations.py", title="Annotations", icon=":material/database_upload:")
    requirements = st.Page("pages/upload/requirements.py", title="Requirements", icon=":material/database_upload:")
    report = st.Page("pages/report.py", title="Report", icon=":material/publish:")
    visualization = st.Page("services/visualisation/visualize_vectors.py", title="Visualize vectors", icon=":material/dataset:")
    pages = {
        "Upload": [annotations, requirements],
        "Inspect": [report, visualization],
    }
    pg = st.navigation(pages)

    pg.run()

