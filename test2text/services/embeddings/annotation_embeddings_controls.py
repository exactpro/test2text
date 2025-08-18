from typing import Callable

from test2text.services.db import get_db_client

BATCH_SIZE = 30


def count_all_annotations() -> int:
    db = get_db_client()
    count = db.conn.execute("SELECT COUNT(*) FROM Annotations").fetchone()[0]
    return count


def count_embedded_annotations() -> int:
    db = get_db_client()
    count = db.conn.execute(
        "SELECT COUNT(*) FROM Annotations WHERE embedding IS NOT NULL"
    ).fetchone()[0]
    return count


OnProgress = Callable[[float], None]


def embed_annotations(*_, embed_all=False, on_progress: OnProgress = None):
    from .embed import embed_annotations_batch

    db = get_db_client()
    annotations_count = count_all_annotations()
    embedded_annotations_count = count_embedded_annotations()
    if embed_all:
        annotations_to_embed = annotations_count
    else:
        annotations_to_embed = annotations_count - embedded_annotations_count

    batch = []

    def write_batch(batch: list[tuple[int, str]]):
        embeddings = embed_annotations_batch([annotation for _, annotation in batch])
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
