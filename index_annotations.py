import csv
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
from test2text.db import DbClient
from test2text.embeddings.embed import embed_annotations_batch

BATCH_SIZE = 100

if __name__ == "__main__":
    db = DbClient("./private/requirements.db")
    annotations_folder = Path("./private/annotations")
    # Write annotations to the database
    for i, file in enumerate(os.listdir(annotations_folder)):
        logging.info(f"Processing file {i + 1}: {file}")
        with open(
            annotations_folder / file, newline="", encoding="utf-8", mode="r"
        ) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                [summary, _, test_script, test_case, *_] = row
                anno_id = db.annotations.get_or_insert(summary=summary)
                tc_id = db.test_cases.get_or_insert(
                    test_script=test_script, test_case=test_case
                )
                db.cases_to_annos.insert(case_id=tc_id, annotation_id=anno_id)
    db.conn.commit()
    # Embed annotations
    annotations_count = db.conn.execute("""
    SELECT COUNT(*) FROM Annotations
    """).fetchone()[0]
    annotations = db.conn.execute("""
    SELECT id, summary FROM Annotations
    """)

    batch = []

    def write_batch():
        global batch
        embeddings = embed_annotations_batch([annotation for _, annotation in batch])
        for i, (anno_id, annotation) in enumerate(batch):
            embedding = embeddings[i]
            db.conn.execute(
                """
                    UPDATE Annotations
                    SET embedding = ?
                    WHERE id = ?
                    """,
                (embedding, anno_id),
            )
        db.conn.commit()
        batch = []

    for i, (anno_id, summary) in enumerate(annotations.fetchall()):
        if i % 100 == 0:
            logging.info(f"Processing annotation {i + 1}/{annotations_count}")
        batch.append((anno_id, summary))
        if len(batch) == BATCH_SIZE:
            write_batch()
    write_batch()
    # Check annotations
    cursor = db.conn.execute("""
    SELECT COUNT(*) FROM Annotations
    """)
    print(cursor.fetchone())
