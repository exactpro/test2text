import csv
import logging

logging.basicConfig(level=logging.DEBUG)
from test2text.db import DbClient
from test2text.embeddings.embed import embed_requirements_batch

BATCH_SIZE = 100

if __name__ == "__main__":
    db = DbClient("./private/requirements.db")
    # Index requirements
    with open(
        "./private/TRACEABILITY MATRIX.csv", newline="", encoding="utf-8", mode="r"
    ) as csvfile:
        reader = csv.reader(csvfile)
        for _ in range(3):
            next(reader)
        batch = []
        last_requirement = ""

        def write_batch():
            global batch
            embeddings = embed_requirements_batch(
                [requirement for _, requirement in batch]
            )
            for i, (external_id, requirement) in enumerate(batch):
                embedding = embeddings[i]
                db.requirements.insert(requirement, embedding, external_id)
            db.conn.commit()
            batch = []

        for row in reader:
            [external_id, requirement, *_] = row
            if requirement.startswith("..."):
                requirement = last_requirement + requirement[3:]
            last_requirement = requirement
            batch.append((external_id, requirement))
            if len(batch) == BATCH_SIZE:
                write_batch()
        write_batch()
    # Check requirements
    cursor = db.conn.execute("""
    SELECT COUNT(*) FROM Requirements
    """)
    print(cursor.fetchone())
