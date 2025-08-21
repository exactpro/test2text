from itertools import groupby
import numpy as np
import streamlit as st
from sqlite_vec import serialize_float32

from test2text.services.utils.math_utils import round_distance

SUMMARY_LENGTH = 100


def make_a_report():
    from test2text.services.db import get_db_client

    with get_db_client() as db:
        from test2text.services.embeddings.embed import embed_requirement
        from test2text.services.utils import unpack_float32
        from test2text.services.visualisation.visualize_vectors import (
            minifold_vectors_2d,
            plot_2_sets_in_one_2d,
            minifold_vectors_3d,
            plot_2_sets_in_one_3d,
        )

        st.header("Test2Text Report")

        def write_annotations(current_annotations: set[tuple]):
            st.write("id,", "Summary,", "Distance")
            for anno_id, anno_summary, _, distance in current_annotations:
                st.write(anno_id, anno_summary, round_distance(distance))

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

            where_clauses = []
            params = []

            if filter_id.strip():
                where_clauses.append("Requirements.id = ?")
                params.append(filter_id.strip())

            if filter_summary.strip():
                where_clauses.append("Requirements.summary LIKE ?")
                params.append(f"%{filter_summary.strip()}%")

            distance_sql = ""
            distance_order_sql = ""
            query_embedding_bytes = None
            if filter_embedding.strip():
                query_embedding = embed_requirement(filter_embedding.strip())
                query_embedding_bytes = serialize_float32(query_embedding)
                distance_sql = ", vec_distance_L2(embedding, ?) AS distance"
                distance_order_sql = "distance ASC, "

        with st.container(border=True):
            st.session_state.update({"req_form_submitting": True})
            data = db.get_ordered_values_from_requirements(
                distance_sql,
                where_clauses,
                distance_order_sql,
                params + [query_embedding_bytes] if distance_sql else params,
            )

            if distance_sql:
                requirements_dict = {
                    f"{req_external_id} {summary[:SUMMARY_LENGTH]}... [smart search d={round_distance(distance)}]": req_id
                    for (req_id, req_external_id, summary, distance) in data
                }
            else:
                requirements_dict = {
                    f"{req_external_id} {summary[:SUMMARY_LENGTH]}...": req_id
                    for (req_id, req_external_id, summary) in data
                }

            st.subheader("Choose 1 of filtered requirements")
            option = st.selectbox(
                "Choose a requirement to work with",
                requirements_dict.keys(),
                key="filter_req_id",
            )

            if option:
                clause = "Requirements.id = ?"
                if clause in where_clauses:
                    idx = where_clauses.index(clause)
                    params.insert(idx, requirements_dict[option])
                else:
                    where_clauses.append(clause)
                    params.append(requirements_dict[option])

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

                if filter_radius:
                    where_clauses.append("distance <= ?")
                    params.append(f"{filter_radius}")

                if filter_limit:
                    params.append(f"{filter_limit}")

                rows = db.join_all_tables_by_requirements(where_clauses, params)

                if not rows:
                    st.error(
                        "There is no requested data to inspect.\n"
                        "Please check filters, completeness of the data or upload new annotations and requirements."
                    )
                    return None

                for (
                    req_id,
                    req_external_id,
                    req_summary,
                    req_embedding,
                ), group in groupby(rows, lambda x: x[0:4]):
                    st.divider()
                    with st.container():
                        st.subheader(f" Inspect Requirement {req_external_id}")
                        st.write(req_summary)
                        current_test_cases = dict()
                        for (
                            _,
                            _,
                            _,
                            _,
                            anno_id,
                            anno_summary,
                            anno_embedding,
                            distance,
                            case_id,
                            test_script,
                            test_case,
                        ) in group:
                            current_annotation = current_test_cases.get(
                                test_case, set()
                            )
                            current_test_cases.update({test_case: current_annotation})
                            current_test_cases[test_case].add(
                                (anno_id, anno_summary, anno_embedding, distance)
                            )

                        t_cs, anno, viz = st.columns(3)
                        with t_cs:
                            with st.container(border=True):
                                st.write("Test Cases")
                                st.info("Test cases of chosen Requirement")
                                st.radio(
                                    "Test cases name",
                                    current_test_cases.keys(),
                                    key="radio_choice",
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

                            if st.session_state["radio_choice"]:
                                with anno:
                                    with st.container(border=True):
                                        st.write("Annotations")
                                        st.info(
                                            "List of Annotations for chosen Test case"
                                        )
                                        write_annotations(
                                            current_annotations=current_test_cases[
                                                st.session_state["radio_choice"]
                                            ]
                                        )
                                with viz:
                                    with st.container(border=True):
                                        st.write("Visualization")
                                        select = st.selectbox(
                                            "Choose type of visualization", ["2D", "3D"]
                                        )
                                        anno_embeddings = [
                                            unpack_float32(anno_emb)
                                            for _, _, anno_emb, _ in current_test_cases[
                                                st.session_state["radio_choice"]
                                            ]
                                        ]
                                        anno_labels = [
                                            f"{anno_id} {anno_sum[:SUMMARY_LENGTH]}"
                                            for anno_id, anno_sum, _, _ in current_test_cases[
                                                st.session_state["radio_choice"]
                                            ]
                                        ]
                                        requirement_vectors = np.array(
                                            [np.array(unpack_float32(req_embedding))]
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
                                                first_labels=[f"{req_external_id}"],
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
                                                first_labels=[f"{req_external_id}"],
                                                second_labels=anno_labels,
                                            )


if __name__ == "__main__":
    make_a_report()
