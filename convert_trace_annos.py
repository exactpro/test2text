import logging
import csv
from test2text.db import DbClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trace_test_cases_to_annos_and_save_csv(db_path, csv_path):
    db = DbClient(db_path)
    db.case_to_annos.init_table()
    case_to_annos = db.conn.execute("""
                    SELECT c.case_id, GROUP_CONCAT(a.summary, ", ")
                    FROM CasesToAnnos as c
                    JOIN Annotations as a ON c.annotation_id == a.id
                    GROUP BY case_id;
                """)

    logger.info("Writing resulted table to CSV and inserting into case_to_annos table...")
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['case_id', 'annotations'])
        for i, (case_id, annotations) in enumerate(case_to_annos.fetchall()):
            db.case_to_annos.insert(case_id=case_id, annotations=annotations)
            writer.writerow([case_id, annotations])

    db.conn.commit()
    logger.info(f"Inserted testcase-annotations pairs to database.")
    logger.info(f"CSV file with matches written to {csv_path}")


if __name__ == '__main__':
    db_path = './private/requirements.db'
    csv_path = './private/anno_req_min_matches.csv'
    trace_test_cases_to_annos_and_save_csv(db_path, csv_path)




