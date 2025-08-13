import csv
import io

import streamlit as st

from test2text.services.db import DbClient
from test2text.services.embeddings.embed import embed_annotations_batch

BATCH_SIZE = 100


def index_annotations_from_files(files: list):
    db = DbClient("./private/requirements.db")
    st.subheader("Processing files:")
    file_order, file_name, proc_file = st.columns(3)
    with file_order:
        st.write("Number")
    with file_name:
        st.write("File name")
    with proc_file:
        st.write("Processing file")

    for i, file in enumerate(files):
        file_order, file_name, proc_file = st.columns(3)
        with file_order:
            st.write(f"{i + 1}/{len(files)}")
        with file_name:
            st.write(f"{file.name}")
        stringio = io.StringIO(file.getvalue().decode("utf-8"))
        reader = csv.reader(stringio)
        insertions = []

        if not list(reader):
            with proc_file:
                st.warning(f"The uploaded CSV file {file.name} is empty.")
            continue
        with proc_file:
            file_progress_bar = st.progress(0)
        count_rows = len(list(reader))
        for i, row in enumerate(reader):
            file_progress_bar.progress(round(i*100/count_rows))
            [summary, _, test_script, test_case, *_] = row
            anno_id = db.annotations.get_or_insert(summary=summary)
            tc_id = db.test_cases.get_or_insert(
                test_script=test_script, test_case=test_case
            )
            insertions.append(db.cases_to_annos.insert(case_id=tc_id, annotation_id=anno_id))

    db.conn.commit()
    # Embed annotations
    annotations_count = db.conn.execute("""
    SELECT COUNT(*) FROM Annotations
    """).fetchone()[0]
    annotations = db.conn.execute("""
    SELECT  Annotations.id as anno_id,
            Annotations.summary as summary,
            TestCases.id as case_id,
            TestCases.test_case as case_name
    FROM Annotations
        JOIN CasesToAnnos ON Annotations.id = CasesToAnnos.annotation_id
        JOIN TestCases ON TestCases.id = CasesToAnnos.case_id
    """)

    anno_batch = []
    tc_batch = []

    def write_batch(batch, db_table_name: str):
        embeddings = embed_annotations_batch([text for _, text in batch])
        for i, (entry_id, text) in enumerate(batch):
            embedding = embeddings[i]
            db.conn.execute(
                f"""
                    UPDATE {db_table_name}
                    SET embedding = ?
                    WHERE id = ?
                    """,
                (embedding, entry_id),
            )
        db.conn.commit()

    st.subheader("Processing annotations:")
    progress_bar = st.progress(0, text="Processing annotation:")
    for i, (anno_id, summary, case_id, case_name) in enumerate(annotations.fetchall()):
        progress_bar.progress(round((i+1) * 100/annotations_count), text="Processing annotation:")
        anno_batch.append((anno_id, summary))
        tc_batch.append((case_id, case_name))
        if len(anno_batch) == BATCH_SIZE:
            write_batch(anno_batch, "Annotations")
            write_batch(tc_batch, "TestCases")
            anno_batch = []
            tc_batch = []

    write_batch(anno_batch, "Annotations")
    write_batch(tc_batch, "TestCases")

    # Check annotations
    cursor = db.conn.execute("""
    SELECT COUNT(*) FROM Annotations
    """)
    return cursor.fetchone()

