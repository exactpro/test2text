import csv
import io
from collections.abc import Callable

from streamlit.delta_generator import DeltaGenerator

from test2text.services.db import get_db_client

BATCH_SIZE = 100

OnFileStart = Callable[[str, str], DeltaGenerator]


def index_annotations_from_files(files: list, *_, on_file_start: OnFileStart = None):
    with get_db_client() as db:
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

        return None
