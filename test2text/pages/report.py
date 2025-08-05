from itertools import groupby

import streamlit as st
from test2text.services.db import DbClient


def add_new_line(summary):
    return summary.replace("\n", "<br>")


def make_a_report():
        st.header("Test2Text Report")

        db = DbClient("./private/requirements.db")

        st.subheader("Table of Contents")

        data = db.conn.execute("""
        SELECT
            Requirements.id as req_id,
            Requirements.external_id as req_external_id,
            Requirements.summary as req_summary,

            Annotations.id as anno_id,
            Annotations.summary as anno_summary,

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
        ORDER BY
            Requirements.id, AnnotationsToRequirements.cached_distance, TestCases.id
        """)

        current_annotations = {}
        current_test_scripts = set()

        def write_requirement(req_id, req_external_id, req_summary,
                              current_annotations: set[tuple], current_test_scripts: set):
            if req_id is None and req_external_id is None:
                return False

            with st.expander(f"#{req_id} Requirement {req_external_id}"):
                st.subheader(f"Requirement {req_external_id}")
                st.html(f"<p>{add_new_line(req_summary)}</p>")
                st.subheader("Annotations")
                anno, summary, dist = st.columns(3)
                with anno:
                    st.write("Annonation's id")
                with summary:
                    st.write("Summary")
                with dist:
                    st.write("Distance")
                for anno_id, anno_summary, distance in current_annotations:
                    anno, summary, dist = st.columns(3)
                    with anno:
                        st.write(f"{anno_id}")
                    with summary:
                        st.html(
                            f"{add_new_line(anno_summary)}"
                        )
                    with dist:
                        st.write(round(distance, 2))

                st.subheader("Test Scripts")
                for test_script in current_test_scripts:
                    st.markdown(f"- {test_script}")

        progress_bar = st.empty()
        rows = data.fetchall()
        if not rows:
            st.error("There is no data to inspect.\nPlease upload annotations.")
            return None
        max_progress = len(rows)
        index = 0
        for (req_id, req_external_id, req_summary), group in groupby(rows, lambda x: x[0:3]):
            current_annotations = set()
            current_test_scripts = set()
            index += 1
            for _, _, _, anno_id, anno_summary, distance, case_id, test_script, test_case in group:
                current_annotations.add((anno_id, anno_summary, distance))
                current_test_scripts.add(test_script)
            write_requirement(req_id=req_id, req_external_id=req_external_id,  req_summary=req_summary,
                              current_annotations=current_annotations, current_test_scripts=current_test_scripts)


            progress_bar.progress(round(index*100/max_progress), text="Processing...")
        progress_bar.empty()
        db.conn.close()


if __name__ == "__main__":
    make_a_report()
