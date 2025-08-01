
import streamlit as st


def add_logo():
    st.markdown(
        """
        <style>
             [data-testid="stSidebarNav"] {
                background-image: url();
                background-repeat: no-repeat;
                padding-top: 10px;
                background-position: 20px 20px;
            }
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
    st.set_page_config(page_title="Test2Text App", layout="wide", initial_sidebar_state="auto")
    add_logo()

    annotations = st.Page("test2text/pages/upload/annotations.py",
                          title="Annotations", icon=":material/database_upload:")
    requirements = st.Page("test2text/pages/upload/requirements.py",
                           title="Requirements", icon=":material/database_upload:")
    cache_distances = st.Page("test2text/services/embeddings/cache_distances.py",
                              title="Cache Distances", icon=":material/cached:")
    report = st.Page("test2text/pages/report.py",
                     title="Report", icon=":material/publish:")
    visualization = st.Page("test2text/services/visualisation/visualize_vectors.py",
                            title="Visualize Vectors", icon=":material/dataset:")
    pages = {
        "Upload": [annotations, requirements],
        "Update": [cache_distances],
        "Inspect": [report, visualization],
    }
    pg = st.navigation(pages)

    pg.run()

