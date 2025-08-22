import logging
import csv
import io
import streamlit as st
from test2text.services.db import get_db_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMPTY = ""


def is_empty(value):
    return True if value == EMPTY else False


def write_table_row(*args, **kwargs):
    count = len(args)
    if count == 0:
        return False
    columns = st.columns(count)
    for i, col in enumerate(columns):
        with col:
            st.write(args[i])
    return True


def trace_test_cases_to_annos(trace_files: list):
    with get_db_client() as db:
        st.info(
            "Reading trace files and inserting test case + annotations pairs into database..."
        )
        write_table_row(
            "File name",
            "Extracted pairs test cases + annotations",
            "Inserted to data base",
            "Ignored (dublicates or wrong id)",
        )
        for i, file in enumerate(trace_files):
            stringio = io.StringIO(file.getvalue().decode("utf-8"))
            reader = csv.reader(stringio)
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
                        case_id = db.test_cases.get_or_insert(
                            test_script=test_script, test_case=current_tc
                        )
                        annotation_id = db.annotations.get_or_insert(
                            summary=concat_summary
                        )
                        insertions.append(
                            db.cases_to_annos.insert(
                                case_id=case_id, annotation_id=annotation_id
                            )
                        )
                else:
                    if not is_empty(row[global_columns.index("TestCase")]):
                        if current_tc != row[global_columns.index("TestCase")]:
                            current_tc = row[global_columns.index("TestCase")]
                        if is_empty(test_script) and not is_empty(
                            row[global_columns.index("TestScript")]
                        ):
                            test_script = row[global_columns.index("TestScript")]
                        concat_summary += row[0]
            write_table_row(
                file.name,
                len(insertions),
                sum(insertions),
                len(insertions) - sum(insertions),
            )
