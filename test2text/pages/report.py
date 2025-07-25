import streamlit as st
from test2text.services.db import DbClient


def add_new_line(summary):
    return summary.replace("\n", "<br>")

# Data structure to store pages
pages = {}

def add_page(page_name):
    pages[page_name] = ""


def make_a_report():
        st.header("Test2Text Report")

        db = DbClient("./private/requirements.db")
        all_reqs_count = db.conn.execute(
            "SELECT COUNT(*) FROM Requirements"
        ).fetchone()[0]

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

        current_req_id = None
        current_annotations = {}
        current_test_scripts = set()

        def write_requirement():
            with st.expander(f"#{req_id} Requirement {req_external_id}"):
                st.html(f"""
                                <h2 id="req_{current_req_id}">Requirement {current_req_external_id} ({current_req_id})</h2>
                                <p>{add_new_line(req_summary)}</p>
                                <h3>Annotations</h3>
                                <ul>
                                """)
                for anno_id, (anno_summary, distance) in current_annotations.items():
                    st.html(
                        f"<li>Annotation {anno_id} (distance: {distance:.3f}): <p>{add_new_line(anno_summary)}</p></li>"
                    )
                st.html("</ul>")
                st.html("<h3>Test Scripts</h3><ul>")
                for test_script in current_test_scripts:
                    st.html(f"<li>{test_script}</li>")
                st.html("</ul>")
        progress_bar = st.progress(0, "Processing...")
        if not data.fetchall():
            st.error("There is no data to inspect.\nPlease upload annotations.")
            return None
        max_progress = len(data.fetchall())
        for i, row in enumerate(data.fetchall()):
            (
                req_id,
                req_external_id,
                req_summary,
                anno_id,
                anno_summary,
                distance,
                case_id,
                test_script,
                test_case,
            ) = row
            if req_id != current_req_id:
                if current_req_id is not None:
                    write_requirement()
                current_req_id = req_id
                current_req_external_id = req_external_id
                current_annotations = {}
                current_test_scripts = set()
            progress_bar.progress(round(i*100/max_progress))
            current_annotations[anno_id] = (anno_summary, distance)
            current_test_scripts.add(test_script)
        write_requirement()



if __name__ == "__main__":
    make_a_report()
