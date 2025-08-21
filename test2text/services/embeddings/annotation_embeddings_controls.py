from typing import Callable

from test2text.services.db import get_db_client

BATCH_SIZE = 30


OnProgress = Callable[[float], None]


def embed_annotations(*_, embed_all=False, on_progress: OnProgress = None):
    with get_db_client() as db:
        from .embed import embed_annotations_batch

        annotations_count = db.count_all_entries_in_table("Annotations")
        embedded_annotations_count = db.count_embedded_entries_in_table("Annotations")
        if embed_all:
            annotations_to_embed = annotations_count
        else:
            annotations_to_embed = annotations_count - embedded_annotations_count

        batch = []

        def write_batch(batch: list[tuple[int, str]]):
            embeddings = embed_annotations_batch(
                [annotation for _, annotation in batch]
            )
            for i, (anno_id, annotation) in enumerate(batch):
                embedding = embeddings[i]
                db.annotations.set_embedding(anno_id, embedding)
            db.conn.commit()

        annotations = db.conn.execute(f"""
        SELECT id, summary FROM Annotations
        {"WHERE embedding IS NULL" if not embed_all else ""}
        """)

        for i, (anno_id, summary) in enumerate(annotations.fetchall()):
            if on_progress:
                on_progress((i + 1) / annotations_to_embed)
            batch.append((anno_id, summary))
            if len(batch) == BATCH_SIZE:
                write_batch(batch)
                batch = []

        write_batch(batch)
