import numpy as np
import streamlit as st

from test2text.services.utils.math_utils import round_distance
from test2text.services.repositories import (
    test_cases as tc_repo,
    requirements as req_repo,
    annotations as an_repo,
)


SUMMARY_LENGTH = 100


def make_a_tc_report():
    from test2text.services.db import get_db_client

    with get_db_client() as db:
        from test2text.services.utils import unpack_float32
        from test2text.services.visualisation.visualize_vectors import (
            minifold_vectors_2d,
            plot_2_sets_in_one_2d,
            minifold_vectors_3d,
            plot_2_sets_in_one_3d,
        )

        st.header("Test2Text Report")

        with st.container(border=True):
            st.subheader("Filter test cases")
            with st.expander("🔍 Filters"):
                summary, embed = st.columns(2)
                with summary:
                    filter_summary = st.text_input(
                        "Text content", value="", key="filter_summary"
                    )
                    st.info("Search concrete phrases using SQL like expressions")
                with embed:
                    filter_embedding = st.text_input(
                        "Smart rearch", value="", key="filter_embedding"
                    )
                    st.info("Search using embeddings")

        with st.container(border=True):
            st.session_state.update({"tc_form_submitting": True})
            test_cases = tc_repo.fetch_filtered_test_cases(
                db, text_content=filter_summary, smart_search_query=filter_embedding
            )
            test_cases = {
                tc_id: (test_script, test_case)
                for tc_id, test_script, test_case in test_cases
            }

            st.subheader("Choose ONE of filtered test cases")
            selected_test_case = st.selectbox(
                "Choose a requirement to work with",
                test_cases.keys(),
                key="filter_tc_id",
                format_func=lambda x: test_cases[x][1],
            )

            if selected_test_case:
                st.subheader("Filter Requirements")

                with st.expander("🔍 Filters"):
                    radius, limit = st.columns(2)
                    with radius:
                        filter_radius = st.number_input(
                            "Insert a radius",
                            value=1.00,
                            step=0.01,
                            key="filter_radius",
                        )
                        st.info("Max distance to annotation")
                    with limit:
                        filter_limit = st.number_input(
                            "Requirement's limit to show",
                            min_value=1,
                            max_value=15,
                            value=15,
                            step=1,
                            key="filter_limit",
                        )
                        st.info("Limit of selected requirements")

                annotations = an_repo.fetch_annotations_by_test_case(
                    db, selected_test_case
                )
                annotations_dict = {
                    anno_id: (anno_summary, anno_embedding)
                    for anno_id, anno_summary, anno_embedding in annotations
                }

                if not annotations_dict:
                    st.error(
                        "There is no requested data to inspect.\n"
                        "Please check filters, completeness of the data or upload new annotations and requirements."
                    )
                else:
                    st.divider()
                    with st.container():
                        st.subheader(
                            f"Inspect #{selected_test_case} Test case '{test_cases[selected_test_case][1]}'"
                        )
                        st.write(
                            f"From test script {test_cases[selected_test_case][0]}"
                        )

                        t_cs, anno, viz = st.columns(3)
                        with t_cs:
                            with st.container(border=True):
                                st.write("Annotations")
                                st.info("Annotations linked to chosen Test case")
                                chosen_annotation = st.radio(
                                    "Annotation's id + summary",
                                    annotations_dict.keys(),
                                    key="chosen_annotation",
                                    format_func=lambda x: f"[{x}] {annotations_dict[x][0][:SUMMARY_LENGTH]}",
                                )
                                st.markdown(
                                    """
                                               <style>
                                                      .stRadio > div {
                                                                   max-width: 100%;
                                                                   word-break: break-word;
                                                                   white-space: normal;
                                                               }
                                                      </style>
                                           """,
                                    unsafe_allow_html=True,
                                )

                            if chosen_annotation:
                                requirements = (
                                    req_repo.fetch_requirements_by_annotation(
                                        db,
                                        annotation_id=chosen_annotation,
                                        radius=filter_radius,
                                        limit=filter_limit,
                                    )
                                )
                                reqs_dict = {
                                    req_id: (
                                        req_external_id,
                                        req_summary,
                                        req_emb,
                                        distance,
                                    )
                                    for req_id, req_external_id, req_summary, req_emb, distance in requirements
                                }
                                with anno:
                                    with st.container(border=True):
                                        st.write("Requirements")
                                        st.info(
                                            "Found Requirements for chosen annotation"
                                        )
                                        st.write("External id,", "Summary,", "Distance")
                                        for (
                                            req_external_id,
                                            req_summary,
                                            _,
                                            distance,
                                        ) in reqs_dict.values():
                                            st.write(
                                                req_external_id,
                                                req_summary,
                                                round_distance(distance),
                                            )
                                with viz:
                                    with st.container(border=True):
                                        st.write("Visualization")
                                        select = st.selectbox(
                                            "Choose type of visualization", ["2D", "3D"]
                                        )
                                        req_embeddings = [
                                            unpack_float32(req_emb)
                                            for _, _, req_emb, _ in reqs_dict.values()
                                        ]
                                        req_labels = [
                                            req_ext_id or req_id
                                            for req_id, (
                                                req_ext_id,
                                                _,
                                                _,
                                                _,
                                            ) in reqs_dict.items()
                                        ]
                                        annotation_vectors = np.array(
                                            [
                                                np.array(
                                                    unpack_float32(
                                                        annotations_dict[
                                                            chosen_annotation
                                                        ][1]
                                                    )
                                                )
                                            ]
                                        )
                                        requirement_vectors = np.array(req_embeddings)
                                        if select == "2D":
                                            plot_2_sets_in_one_2d(
                                                minifold_vectors_2d(annotation_vectors),
                                                minifold_vectors_2d(
                                                    requirement_vectors
                                                ),
                                                first_title="Annotation",
                                                second_title="Requirements",
                                                first_labels=chosen_annotation,
                                                second_labels=req_labels,
                                            )
                                        else:
                                            reqs_vectors_3d = minifold_vectors_3d(
                                                requirement_vectors
                                            )
                                            anno_vectors_3d = minifold_vectors_3d(
                                                annotation_vectors
                                            )
                                            plot_2_sets_in_one_3d(
                                                anno_vectors_3d,
                                                reqs_vectors_3d,
                                                first_title="Annotation",
                                                second_title="Requirements",
                                                first_labels=chosen_annotation,
                                                second_labels=req_labels,
                                            )


if __name__ == "__main__":
    make_a_tc_report()
