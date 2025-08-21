from itertools import groupby
import numpy as np
import streamlit as st
from sqlite_vec import serialize_float32

from test2text.services.db import get_db_client
from test2text.services.utils import unpack_float32
from test2text.services.visualisation.visualize_vectors import (
    minifold_vectors_2d,
    plot_2_sets_in_one_2d,
    minifold_vectors_3d,
    plot_2_sets_in_one_3d,
)


def make_a_report():
    with get_db_client() as db:
        from test2text.services.embeddings.embed import embed_requirement

        st.header("Test2Text Report")

        def write_annotations(current_annotations: set[tuple]):
            anno, summary, dist = st.columns(3)
            with anno:
                st.write("Annonation's id")
            with summary:
                st.write("Summary")
            with dist:
                st.write("Distance")
            for anno_id, anno_summary, _, distance in current_annotations:
                anno, summary, dist = st.columns(3)
                with anno:
                    st.write(f"{anno_id}")
                with summary:
                    st.write(anno_summary)
                with dist:
                    st.write(round(distance, 2))

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

            where_sql = ""
            if where_clauses:
                where_sql = f"WHERE {' AND '.join(where_clauses)}"

        with st.container(border=True):
            st.session_state.update({"req_form_submitting": True})
            sql = f"""
                    SELECT
                        Requirements.id as req_id,
                        Requirements.external_id as req_external_id,
                        Requirements.summary as req_summary
                        {distance_sql}
                    FROM
                        Requirements
                    {where_sql}
                    ORDER BY
                        {distance_order_sql}Requirements.id
                    """
            data = db.conn.execute(
                sql, params + [query_embedding_bytes] if distance_sql else params
            )
            if distance_sql:
                requirements_dict = {
                    f"#{req_id} Requirement {req_external_id} [smart search d={distance}]": req_id
                    for (req_id, req_external_id, _, distance) in data.fetchall()
                }
            else:
                requirements_dict = {
                    f"#{req_id} Requirement {req_external_id}": req_id
                    for (req_id, req_external_id, _) in data.fetchall()
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

                where_sql = ""
                if where_clauses:
                    where_sql = f"WHERE {' AND '.join(where_clauses)}"

                sql = f"""
                    SELECT
                        Requirements.id as req_id,
                        Requirements.external_id as req_external_id,
                        Requirements.summary as req_summary,
                        Requirements.embedding as req_embedding,
            
                        Annotations.id as anno_id,
                        Annotations.summary as anno_summary,
                        Annotations.embedding as anno_embedding,
            
                        AnnotationsToRequirements.cached_distance as distance,
            
                        TestCases.id as case_id,
                        TestCases.test_script as test_script,
                        TestCases.test_case as test_case
                    FROM
                        Requirements
                            JOIN AnnotationsToRequirements ON Requirements.id = AnnotationsToRequirements.requirement_id
                            JOIN Annotations ON Annotations.id = AnnotationsToRequirements.annotation_id
                            JOIN CasesToAnnos ON Annotations.id = CasesToAnnos.annotation_id
                            JOIN TestCases ON TestCases.id = CasesToAnnos.case_id
                    {where_sql}
                    ORDER BY
                        Requirements.id, AnnotationsToRequirements.cached_distance, TestCases.id
                    LIMIT ?
                    """
                data = db.conn.execute(sql, params)
                rows = data.fetchall()
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
                                                first_color="red",
                                                second_color="green",
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
                                            )


if __name__ == "__main__":
    make_a_report()
