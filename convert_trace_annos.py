import logging
import csv
from pathlib import Path
from test2text.services.db import get_db_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMPTY = ""


def is_empty(value):
    return True if value == EMPTY else False


def trace_test_cases_to_annos(db_path: Path, trace_file_path: Path):
    db = get_db_client()

    insertions = list()
    logger.info("Reading trace file and inserting annotations into table...")
    with open(trace_file_path, mode="r", newline="", encoding="utf-8") as trace_file:
        reader = csv.reader(trace_file)
        current_tc = EMPTY
        concat_summary = EMPTY
        test_script = EMPTY
        global_columns = next(reader)
        for row in reader:
            if row[0] == "TestCaseStart":
                current_tc = row[1]
                test_script = EMPTY
                concat_summary = EMPTY
                next(reader)
            elif row[0] == "Summary":
                continue
            elif row[0] == "TestCaseEnd":
                if not is_empty(current_tc) and not is_empty(concat_summary):
                    case_id = db.test_cases.get_or_insert(
                        test_script=test_script, test_case=current_tc
                    )
                    annotation_id = db.annotations.get_or_insert(summary=concat_summary)
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

    db.conn.commit()
    logger.info(
        f"Inserted {len(insertions)} testcase-annotations pairs to database. Successful: {sum(insertions)}"
    )


if __name__ == "__main__":
    db_path = Path("./private/requirements.db")
    trace_file_path = Path("./private/annotations/stp_0006.Trace.csv")
    trace_test_cases_to_annos(db_path, trace_file_path)
