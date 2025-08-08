from itertools import groupby
import numpy as np
import streamlit as st

from test2text.services.db import DbClient
from test2text.services.utils import unpack_float32
from test2text.services.visualisation.visualize_vectors import minifold_vectors_2d, plot_vectors_2d, \
    plot_2_sets_in_one_2d


def make_a_tc_report():
    db = DbClient("./private/requirements.db")
    st.header("Test2Text Report")

    def write_requirements(current_requirements: set[tuple]):
        req, summary, dist = st.columns(3)
        with req:
            st.write("Requirements's id")
        with summary:
            st.write("Summary")
        with dist:
            st.write("Distance")

        for req_id, req_external_id, req_summary, _, distance in current_requirements:
            req, summary, dist = st.columns(3)
            with req:
                st.write(f"#{req_id} Requirement {req_external_id}")
            with summary:
                st.write(req_summary)
            with dist:
                st.write(distance)

    with st.container(border=True):
        st.subheader("Filter test cases")
        with st.expander("🔍 Filters"):
            r_id, summary, embed = st.columns(3)
            with r_id:
                filter_id = st.text_input("ID", value="", key="filter_id")
                st.info("Filter by external ID")
            with summary:
                filter_summary = st.text_input("Text content", value="", key="filter_summary")
                st.info("Search concrete phrases using SQL like expressions")
            with embed:
                filter_embedding = st.text_input("Smart rearch", value="", key="filter_embedding")
                st.info("Search using embeddings")

        where_clauses = []
        params = []

        if filter_id.strip():
            where_clauses.append("Testcases.id = ?")
            params.append(filter_id.strip())

        if filter_summary.strip():
            where_clauses.append("Testcases.test_case LIKE ?")
            params.append(f"%{filter_summary.strip()}%")

        # TODO embeddings фильтр не реализован
        if filter_embedding.strip():
            st.info("Фильтрация по embeddings не реализована в демо. Используйте другие фильтры.")

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
                FROM
                    TestCases
                {where_sql}
                ORDER BY
                    TestCases.id
                """
        data = db.conn.execute(sql, params)

        tc_dict = {f"#{tc_id} Testcase {test_case}": tc_id for (tc_id, _, test_case) in data.fetchall()}
        st.subheader("Choose ONE of filtered test casees")
        option = st.selectbox(
            "Choose a requirement to work with",
            tc_dict.keys(),
            key="filter_tc_id"
        )

        if option:

            clause = "Testcases.id = ?"
            if clause in where_clauses:
                idx = where_clauses.index(clause)
                params.insert(idx, tc_dict[option])
            else:
                where_clauses.append(clause)
                params.append(tc_dict[option])

            st.subheader("Filter Requirements")

            with st.expander("🔍 Filters"):
                radius, limit = st.columns(2)
                with radius:
                    filter_radius = st.number_input("Insert a radius",
                                                    value=0.00,
                                                    step=0.01,
                                                    key="filter_radius")
                    st.info("Max distance to annotation")
                with limit:
                    filter_limit = st.number_input(
                        "Requirement's limit to show",
                        min_value=1,
                        max_value=15,
                        value=15,
                        step=1,
                        key="filter_limit"
                    )
                    st.info("Limit of selected requirements")

            if filter_radius:
                where_clauses.append("distance >= ?")
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
                st.error("There is no data to inspect.\n"
                         "Please upload annotations and requirements.")
                return None


            for (tc_id, test_script, test_case), group in groupby(rows, lambda x: x[0:3]):
                st.divider()
                with st.container():
                    st.subheader(f"Inspect #{tc_id} Test case {test_case}")
                    current_annotations = dict()
                    for _, _, _, anno_id, anno_summary, anno_embedding, distance, req_id, req_external_id, req_summary, req_embedding in group:
                        current_annotation = (anno_id, anno_summary, anno_embedding)
                        current_reqs = current_annotations.get(current_annotation, set())
                        current_annotations.update({current_annotation: current_reqs})
                        current_annotations[current_annotation].add((req_id, req_external_id, req_summary, req_embedding, distance))

                    t_cs, anno, viz = st.columns(3)
                    with t_cs:
                        with st.container(border=True):
                            st.write("Annotations")
                            st.markdown("""
                                <style>
                                .stRadio > div {
                                    max-width: 350px;
                                    word-break: break-word;
                                    white-space: pre-line;
                                }
                                </style>
                            """, unsafe_allow_html=True)
                            reqs_by_anno = {f"#{anno_id} Annotation {anno_summary}": (anno_id, anno_summary, anno_embedding) for (anno_id, anno_summary, anno_embedding) in current_annotations.keys()}
                            radio_choice = st.radio("", reqs_by_anno.keys(), key="radio_choice")
                        if radio_choice:
                            with anno:
                                with st.container(border=True):
                                    st.write("Requirements")
                                    write_requirements(current_annotations[reqs_by_anno[radio_choice]])

                            with viz:
                                with st.container(border=True):
                                    anno_dot = np.array(unpack_float32(anno_embedding))
                                    req_embeddings = [
                                        unpack_float32(req_emb)
                                        for _, _, _, req_emb,_ in current_annotations[reqs_by_anno[radio_choice]]
                                    ]

                                    req_embeddings_np = np.array(req_embeddings)
                                    plot_2_sets_in_one_2d(minifold_vectors_2d(np.array([anno_dot])),
                                                          minifold_vectors_2d(req_embeddings_np),
                                                          "Annotations", "Requirements",first_color="red", second_color="green")

    db.conn.close()
 
 
if __name__ == "__main__":
    make_a_tc_report()