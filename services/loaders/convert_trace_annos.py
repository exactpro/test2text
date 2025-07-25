import logging
import csv
import io
import streamlit as st
from services.db import DbClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMPTY = ""


def is_empty(value):
    return True if value == EMPTY else False


def trace_test_cases_to_annos(trace_files: list):
    db = DbClient('./private/requirements.db')

    st.info("Reading trace files and inserting annotations into table...")
    for i, file in enumerate(trace_files):
        stringio = io.StringIO(file.getvalue().decode("utf-8"))
        reader = csv.DictReader(stringio)
        current_tc = EMPTY
        concat_summary = EMPTY
        test_script = EMPTY
        global_columns = next(reader)
        insertions = list()
        for row in reader:
            if row[0] == "TestCaseStart":
                current_tc = row[1]
                test_script = EMPTY
                concat_summary = EMPTY
            elif row[0] == "Summary":
                continue
            elif row[0] == "TestCaseEnd":
                if not is_empty(current_tc) and not is_empty(concat_summary):
                    case_id = db.test_cases.get_or_insert(test_script=test_script, test_case=current_tc)
                    annotation_id = db.annotations.get_or_insert(summary=concat_summary)
                    insertions.append(db.cases_to_annos.insert(case_id=case_id, annotation_id=annotation_id))
            else:
                if not is_empty(row[global_columns.index("TestCase")]):
                    if current_tc != row[global_columns.index("TestCase")]:
                        current_tc = row[global_columns.index("TestCase")]
                    if is_empty(test_script) and not is_empty(row[global_columns.index("TestScript")]):
                        test_script = row[global_columns.index("TestScript")]
                    concat_summary += row[0]
        st.write(f"File {file.name}: Inserted {len(insertions)} testcase-annotations pairs to database. Successful: {sum(insertions)}.")

    db.conn.commit()






