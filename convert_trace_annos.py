import logging
import csv
from pathlib import Path
from test2text.db import DbClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trace_test_cases_to_annos(db_path: Path, trace_file_path: Path):
    db = DbClient(db_path)
    db.cases_to_annos.init_table()

    test_cases = set()
    logger.info("Reading trace file and inserting annotations into table...")
    with open(trace_file_path, mode='r', newline='', encoding='utf-8') as trace_file:
        reader = csv.DictReader(trace_file)
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

    db.conn.commit()
    logger.info(f"Inserted {len(test_cases)} testcase-annotations pairs to database.")


if __name__ == '__main__':
    db_path = Path('./private/requirements.db')
    trace_file_path = Path('./private/annotations/stp_0006.Trace.csv')
    trace_test_cases_to_annos(db_path, trace_file_path)




