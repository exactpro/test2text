import numpy as np
import streamlit as st

from test2text.services.utils.math_utils import round_distance
from test2text.services.repositories import (
    requirements as requirements_repo,
    test_cases as test_cases_repo,
    annotations as annotations_repo,
)

SUMMARY_LENGTH = 100
LABELS_SUMMARY_LENGTH = 15


def make_a_report():
    from test2text.services.db import get_db_client

    with get_db_client() as db:
        st.header("Test2Text Report")

        with st.container(border=True):
            st.subheader("Filter requirements")
            with st.expander("🔍 Filters"):
                r_id, summary, embed = st.columns(3)
                with r_id:
                    filter_id = st.text_input("ID", value="", key="filter_id")
                    st.info("Filter by external ID")
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
            st.session_state.update({"req_form_submitting": True})
            requirements = requirements_repo.fetch_filtered_requirements(
                db,
                external_id=filter_id,
                text_content=filter_summary,
                smart_search_query=filter_embedding,
            )

            requirements = {
                req_id: (req_external_id, summary)
                for (req_id, req_external_id, summary) in requirements
            }

            st.subheader("Choose 1 of filtered requirements")
            selected_requirement = st.selectbox(
                "Choose a requirement to work with",
                requirements.keys(),
                key="filter_req_id",
                format_func=lambda x: f"{requirements[x][0]} {requirements[x][1][:SUMMARY_LENGTH]}...",
            )

            if selected_requirement:
                requirement = db.requirements.get_by_id_raw(selected_requirement)
                st.subheader("Filter Test cases")

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
                            "Test case limit to show",
                            min_value=1,
                            max_value=15,
                            value=15,
                            step=1,
                            key="filter_limit",
                        )
                        st.info("Limit of selected test cases")

                test_cases = test_cases_repo.fetch_test_cases_by_requirement(
                    db, selected_requirement, filter_radius, filter_limit
                )
                test_cases = {
                    tc_id: (test_script, test_case)
                    for (tc_id, test_script, test_case) in test_cases
                }

                if not test_cases:
                    st.error(
                        "There is no requested data to inspect.\n"
                        "Please check filters, completeness of the data or upload new annotations and requirements."
                    )
                else:
                    from test2text.services.utils import unpack_float32
                    from test2text.services.visualisation.visualize_vectors import (
                        minifold_vectors_2d,
                        plot_2_sets_in_one_2d,
                        minifold_vectors_3d,
                        plot_2_sets_in_one_3d,
                    )

                    st.divider()
                    with st.container():
                        st.subheader(
                            f" Inspect Requirement {requirements[selected_requirement][0]}"
                        )
                        st.write(requirements[selected_requirement][1])

                        t_cs, anno, viz = st.columns(3)
                        with t_cs:
                            with st.container(border=True):
                                st.write("Test Cases")
                                st.info("Test cases of chosen Requirement")
                                st.radio(
                                    "Test cases name",
                                    test_cases.keys(),
                                    key="chosen_test_case",
                                    format_func=lambda tc_id: test_cases[tc_id][1],
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

                            if st.session_state["chosen_test_case"]:
                                annotations = annotations_repo.fetch_annotations_by_test_case_with_distance_to_requirement(
                                    db,
                                    st.session_state["chosen_test_case"],
                                    requirement[3],  # embedding
                                )
                                with anno:
                                    with st.container(border=True):
                                        st.write("Annotations")
                                        st.info(
                                            "List of Annotations for chosen Test case"
                                        )
                                        st.write("id,", "Summary,", "Distance")
                                        for (
                                            anno_id,
                                            anno_summary,
                                            _,
                                            distance,
                                        ) in annotations:
                                            st.write(
                                                anno_id,
                                                anno_summary,
                                                round_distance(distance),
                                            )
                                with viz:
                                    with st.container(border=True):
                                        st.write("Visualization")
                                        select = st.selectbox(
                                            "Choose type of visualization", ["2D", "3D"]
                                        )
                                        anno_embeddings = [
                                            unpack_float32(anno_emb)
                                            for _, _, anno_emb, _ in annotations
                                        ]
                                        anno_labels = [
                                            f"{anno_id}"
                                            for anno_id, _, _, _ in annotations
                                        ]
                                        requirement_vectors = np.array(
                                            [np.array(unpack_float32(requirement[3]))]
                                        )
                                        annotation_vectors = np.array(anno_embeddings)
                                        if select == "2D":
                                            plot_2_sets_in_one_2d(
                                                minifold_vectors_2d(
                                                    requirement_vectors
                                                ),
                                                minifold_vectors_2d(annotation_vectors),
                                                "Requirement",
                                                "Annotations",
                                                first_labels=[f"{requirement[1]}"],
                                                second_labels=anno_labels,
                                            )
                                        else:
                                            reqs_vectors_3d = minifold_vectors_3d(
                                                requirement_vectors
                                            )
                                            anno_vectors_3d = minifold_vectors_3d(
                                                annotation_vectors
                                            )
                                            plot_2_sets_in_one_3d(
                                                reqs_vectors_3d,
                                                anno_vectors_3d,
                                                "Requirement",
                                                "Annotations",
                                                first_labels=[f"{requirement[1]}"],
                                                second_labels=anno_labels,
                                            )


if __name__ == "__main__":
    make_a_report()
