import csv
import io
from collections.abc import Callable

import streamlit as st
from sqlite_vec import serialize_float32
from streamlit.delta_generator import DeltaGenerator

from test2text.services.db import get_db_client
from test2text.services.embeddings.embed import embed_annotations_batch

BATCH_SIZE = 100

OnFileStart = Callable[[str, str], DeltaGenerator]


def index_annotations_from_files(files: list, *_, on_file_start: OnFileStart = None):
    db = get_db_client()

    for i, file in enumerate(files):
        file_counter = None
        if on_file_start:
            file_counter = on_file_start(f"{i + 1}/{len(files)}", file.name)
        stringio = io.StringIO(file.getvalue().decode("utf-8"))
        reader = csv.reader(stringio)
        insertions = []

        for i, row in enumerate(reader):
            if file_counter:
                file_counter.write(i)
            [summary, _, test_script, test_case, *_] = row
            anno_id = db.annotations.get_or_insert(summary=summary)
            tc_id = db.test_cases.get_or_insert(
                test_script=test_script, test_case=test_case
            )
            insertions.append(
                db.cases_to_annos.insert(case_id=tc_id, annotation_id=anno_id)
            )

    db.conn.commit()
    return None
    # Embed annotations
    annotations_count = db.conn.execute("""
    SELECT COUNT(*) FROM Annotations
    """).fetchone()[0]
    annotations = db.conn.execute("""
    SELECT id, summary FROM Annotations
    """)

    batch = []

    def write_batch(batch: list[tuple[int, str]]):
        embeddings = embed_annotations_batch([annotation for _, annotation in batch])
        for i, (anno_id, annotation) in enumerate(batch):
            embedding = embeddings[i]
            db.conn.execute(
                """
                    UPDATE Annotations
                    SET embedding = ?
                    WHERE id = ?
                    """,
                (serialize_float32(embedding), anno_id),
            )
        db.conn.commit()

    st.subheader("Processing annotations:")
    progress_bar = st.progress(0, text="Processing annotation:")
    for i, (anno_id, summary) in enumerate(annotations.fetchall()):
        progress_bar.progress(
            round((i + 1) * 100 / annotations_count), text="Processing annotation:"
        )
        batch.append((anno_id, summary))
        if len(batch) == BATCH_SIZE:
            write_batch(batch)
            batch = []

    write_batch(batch)

    # Check annotations
    cursor = db.conn.execute("""
    SELECT COUNT(*) FROM Annotations
    """)
    return cursor.fetchone()
