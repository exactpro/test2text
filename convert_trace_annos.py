import logging
import csv
from pathlib import Path
from test2text.db import DbClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trace_test_cases_to_annos(db_path: Path, trace_file_path: Path):
    db = DbClient(db_path)

    test_cases = set()
    logger.info("Reading trace file and inserting annotations into table...")
    with open(trace_file_path, mode='r', newline='', encoding='utf-8') as trace_file:
        reader = csv.reader(trace_file)
        current_tc = ""
        concat_summary = ""
        test_script = ""
        global_columns = next(reader)
        for row in reader:
            if row[0] == "TestCaseStart":
                current_tc = row[1]
                test_script = ""
                concat_summary = ""
                if current_tc != "":
                    test_cases.add(current_tc)
                next(reader)
            elif row[0] == "Summary":
                continue
            elif row[0] == "TestCaseEnd":
                if current_tc != "" and concat_summary != "":
                    case_id = db.test_cases.insert(test_script=test_script, test_case=current_tc)
                    annotation_id = db.annotations.insert(summary=concat_summary)
                    db.cases_to_annos.insert(case_id=case_id, annotation_id=annotation_id)
            else:
                if row[global_columns.index("TestCase")] != "":
                    if current_tc != row[global_columns.index("TestCase")]:
                        current_tc = row[global_columns.index("TestCase")]
                        test_cases.add(current_tc)
                    if test_script == "" and row[global_columns.index("TestScript")] != "":
                        test_script = row[global_columns.index("TestScript")]
                    concat_summary += row[0]

    db.conn.commit()
    logger.info(f"Inserted {len(test_cases)} testcase-annotations pairs to database.{[tc for tc in test_cases]}")


if __name__ == '__main__':
    db_path = Path('./private/requirements.db')
    trace_file_path = Path('./private/annotations/stp_0006.Trace.csv')
    trace_test_cases_to_annos(db_path, trace_file_path)




