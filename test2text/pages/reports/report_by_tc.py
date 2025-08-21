from itertools import groupby
import numpy as np
import streamlit as st
from sqlite_vec import serialize_float32

from test2text.services.utils.math_utils import round_distance


def make_a_tc_report():
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

        def write_requirements(current_requirements: set[tuple]):
            st.write("External id,", "Summary,", "Distance")
            for (
                _,
                req_external_id,
                req_summary,
                _,
                distance,
            ) in current_requirements:
                st.write(req_external_id, req_summary, round_distance(distance)
                )

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

            where_clauses = []
            params = []


            if filter_summary.strip():
                where_clauses.append("Testcases.test_case LIKE ?")
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
            st.session_state.update({"tc_form_submitting": True})
            sql = f"""
                    SELECT
                        TestCases.id as case_id,
                        TestCases.test_script as test_script,
                        TestCases.test_case as test_case
                        {distance_sql}
                    FROM
                        TestCases
                    {where_sql}
                    ORDER BY
                        {distance_order_sql}TestCases.id
                    """
            data = db.conn.execute(
                sql, params + [query_embedding_bytes] if distance_sql else params
            )
            if distance_sql:
                tc_dict = {
                    f"{test_case} [smart search d={round_distance(distance)}]": tc_id
                    for (tc_id, _, test_case, distance) in data.fetchall()
                }
            else:
                tc_dict = {
                    test_case: tc_id for (tc_id, _, test_case) in data.fetchall()
                }

            st.subheader("Choose ONE of filtered test cases")
            option = st.selectbox(
                "Choose a requirement to work with", tc_dict.keys(), key="filter_tc_id"
            )

            if option:
                where_clauses.append("Testcases.id = ?")
                params.append(tc_dict[option])

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
                        TestCases.id as case_id,
                        TestCases.test_script as test_script,
                        TestCases.test_case as test_case,
            
                        Annotations.id as anno_id,
                        Annotations.summary as anno_summary,
                        Annotations.embedding as anno_embedding,
            
                        AnnotationsToRequirements.cached_distance as distance,
            
                        Requirements.id as req_id,
                        Requirements.external_id as req_external_id,
                        Requirements.summary as req_summary,
                        Requirements.embedding as req_embedding
                    FROM
                        TestCases
                            JOIN CasesToAnnos ON TestCases.id = CasesToAnnos.case_id
                            JOIN Annotations ON Annotations.id = CasesToAnnos.annotation_id
                            JOIN AnnotationsToRequirements ON Annotations.id = AnnotationsToRequirements.annotation_id
                            JOIN Requirements ON Requirements.id = AnnotationsToRequirements.requirement_id
                    {where_sql}
                    ORDER BY
                        case_id, distance, req_id
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

                for (tc_id, test_script, test_case), group in groupby(
                    rows, lambda x: x[0:3]
                ):
                    st.divider()
                    with st.container():
                        st.subheader(f"Inspect #{tc_id} Test case '{test_case}'")
                        st.write(f"From test script {test_script}")
                        current_annotations = dict()
                        for (
                            _,
                            _,
                            _,
                            anno_id,
                            anno_summary,
                            anno_embedding,
                            distance,
                            req_id,
                            req_external_id,
                            req_summary,
                            req_embedding,
                        ) in group:
                            current_annotation = (anno_id, anno_summary, anno_embedding)
                            current_reqs = current_annotations.get(
                                current_annotation, set()
                            )
                            current_annotations.update(
                                {current_annotation: current_reqs}
                            )
                            current_annotations[current_annotation].add(
                                (
                                    req_id,
                                    req_external_id,
                                    req_summary,
                                    req_embedding,
                                    distance,
                                )
                            )

                        t_cs, anno, viz = st.columns(3)
                        with t_cs:
                            with st.container(border=True):
                                st.write("Annotations")
                                st.info("Annotations linked to chosen Test case")
                                reqs_by_anno = {
                                    f"#{anno_id} {anno_summary}": (
                                        anno_id,
                                        anno_summary,
                                        anno_embedding,
                                    )
                                    for (
                                        anno_id,
                                        anno_summary,
                                        anno_embedding,
                                    ) in current_annotations.keys()
                                }
                                radio_choice = st.radio(
                                    "Annotation's id + summary",
                                    reqs_by_anno.keys(),
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

                            if radio_choice:
                                with anno:
                                    with st.container(border=True):
                                        st.write("Requirements")
                                        st.info(
                                            "Found Requirements for chosen annotation"
                                        )
                                        write_requirements(
                                            current_annotations[
                                                reqs_by_anno[radio_choice]
                                            ]
                                        )
                                with viz:
                                    with st.container(border=True):
                                        st.write("Visualization")
                                        select = st.selectbox(
                                            "Choose type of visualization", ["2D", "3D"]
                                        )
                                        req_embeddings = [
                                            unpack_float32(req_emb)
                                            for _, _, _, req_emb, _ in current_annotations[
                                                reqs_by_anno[radio_choice]
                                            ]
                                        ]
                                        annotation_vectors = np.array(
                                            [np.array(unpack_float32(anno_embedding))]
                                        )
                                        requirement_vectors = np.array(req_embeddings)
                                        if select == "2D":
                                            plot_2_sets_in_one_2d(
                                                minifold_vectors_2d(annotation_vectors),
                                                minifold_vectors_2d(
                                                    requirement_vectors
                                                ),
                                                "Annotation",
                                                "Requirements",
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
                                                anno_vectors_3d,
                                                reqs_vectors_3d,
                                                "Annotation",
                                                "Requirements",
                                            )


if __name__ == "__main__":
    make_a_tc_report()
