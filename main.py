import streamlit as st

from test2text.pages.upload.annotations import  show_annotations
from test2text.pages.upload.requirements import  show_requirements
from test2text.services.embeddings.cache_distances import show_distances_histogram
from test2text.pages.report_by_req import make_a_report
from test2text.pages.report_by_tc import make_a_tc_report
from test2text.services.visualisation.visualize_vectors import  visualize_vectors


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

    annotations = st.Page(show_annotations,
                          title="Annotations", icon=":material/database_upload:")
    requirements = st.Page(show_requirements,
                           title="Requirements", icon=":material/database_upload:")
    cache_distances = st.Page(show_distances_histogram,
                              title="Cache Distances", icon=":material/cached:")
    report_by_req = st.Page(make_a_report,
                     title="Requirement's Report", icon=":material/publish:")
    report_by_tc = st.Page(make_a_tc_report,
                            title="Test cases Report", icon=":material/publish:")
    visualization = st.Page(visualize_vectors,
                            title="Visualize Vectors", icon=":material/dataset:")
    pages = {
        "Upload": [annotations, requirements],
        "Update": [cache_distances],
        "Inspect": [report_by_req, report_by_tc, visualization],
    }
    pg = st.navigation(pages)

    pg.run()

