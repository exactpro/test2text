import logging
import csv
from pathlib import Path

from test2text.db import DbClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trace_test_cases_to_annos_and_save_csv(db_path: Path, trace_file_path: Path, csv_path: Path):
    db = DbClient(db_path)
    db.case_to_annos.init_table()

    test_cases = set()
    logger.info("Reading trace file and inserting annotations into table...")
    with open(trace_file_path, mode='r', newline='', encoding='utf-8') as trace_file:
        content = trace_file.readlines()
        for annotation in content[3:]:
            [summary, _, test_script, test_case, *_] = annotation
            annotation_id = db.annotations.insert(summary)
            case_id = db.test_cases.insert(test_script, test_case)
            db.cases_to_annos.insert(case_id=case_id, annotation_id=annotation_id)
            db.case_to_annos.update_annotations(case_id=case_id, addition=annotation)
            test_cases.add(case_id)

    db.conn.commit()
    logger.info(f"Inserted {len(test_cases)} testcase-annotations pairs to database.")


if __name__ == '__main__':
    db_path = Path('./private/requirements.db')
    csv_path = Path('./private/anno_req_min_matches.csv')
    trace_file_path = Path('./private/annotations/stp_0006.Trace.csv')
    trace_test_cases_to_annos_and_save_csv(db_path, trace_file_path, csv_path)




