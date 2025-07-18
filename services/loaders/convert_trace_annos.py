import logging
import csv
import io
import streamlit as st
from services.db import DbClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trace_test_cases_to_annos(trace_files: list):
    db = DbClient('./private/requirements.db')


    st.info("Reading trace files and inserting annotations into table...")
    for i, file in enumerate(trace_files):
        test_cases = set()
        stringio = io.StringIO(file.getvalue().decode("utf-8"))
        reader = csv.DictReader(stringio)
        current_tc = ""
        concat_summary = ""
        for row in reader:
            if row.get("TestCase", "") != "":
                if current_tc != row["TestCase"]:
                    if current_tc:
                        case_id = db.test_cases.insert(test_script=row["TestScript"], test_case=row["TestCase"])
                        annotation_id = db.annotations.insert(summary=concat_summary)
                        db.cases_to_annos.insert(case_id=case_id, annotation_id=annotation_id)
                        concat_summary = ""
                    current_tc = row["TestCase"]
                    test_cases.add(current_tc)
                concat_summary += row["Summary"]
        st.write(f"File {file.name}: Inserted {len(test_cases)} testcase-annotations pairs to database.")

    db.conn.commit()






