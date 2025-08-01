import csv
import io

import streamlit as st

from test2text.services.db import DbClient
from test2text.services.embeddings.embed import embed_requirements_batch

BATCH_SIZE = 100


def index_requirements_from_files(files: list):
    db = DbClient("./private/requirements.db")

    for i, file in enumerate(files):
        st.info(f"Processing file {i + 1}: {file.name}")
        stringio = io.StringIO(file.getvalue().decode("utf-8"))
        reader = csv.reader(stringio)

        if not list(reader):
            st.warning(f"The uploaded CSV file {file.name} is empty.")
            continue

        if len(list(reader)) <= 3:
            st.warning(f"The uploaded CSV file {file.name}'s content is too short. There are only {len(list(reader))} lines.")
            continue

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
    return cursor.fetchone()


