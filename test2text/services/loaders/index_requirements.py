import csv
import io
from typing import Callable, Optional, Union

from streamlit.runtime.uploaded_file_manager import UploadedFile

from test2text.services.db import get_db_client
from test2text.services.embeddings.embed import embed_requirements_batch

BATCH_SIZE = 100

OnStartFile = Callable[[int, str], None]
OnRequirementWritten = Callable[[Optional[str]], None]


def index_requirements_from_files(
    files: Union[UploadedFile, list[UploadedFile]],
    *args,
    on_start_file: OnStartFile = None,
    on_requirement_written: OnRequirementWritten = None,
) -> tuple[int]:
    db = get_db_client()
    for i, file in enumerate(files):
        if on_start_file:
            on_start_file(i + 1, file.name)
        stringio = io.StringIO(file.getvalue().decode("utf-8"))
        reader = csv.reader(stringio)

        try:
            for _ in range(3):
                next(reader)
        except StopIteration:
            raise ValueError(
                f"The uploaded CSV file {file.name} does not have enough lines. "
                "Please ensure it has at least 3 lines of data."
            )

        batch = []
        last_requirement = ""

        def write_batch():
            nonlocal batch
            embeddings = embed_requirements_batch(
                [requirement for _, requirement in batch]
            )
            for i, (external_id, requirement) in enumerate(batch):
                embedding = embeddings[i]
                db.requirements.insert(requirement, embedding, external_id)
                if on_requirement_written:
                    on_requirement_written(external_id)
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
    return cursor.fetchone()[0]
