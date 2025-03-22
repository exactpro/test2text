import sqlite3
import sqlite_vec

from .tables import RequirementsTable, AnnotationsTable

class DbClient:
    db: sqlite3.Connection

    def __init__(self, file_path: str):
        self.db = sqlite3.connect(file_path)
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self.db.enable_load_extension(False)

        self.requirements = RequirementsTable(self.db)
        self.annotations = AnnotationsTable(self.db)
        self.requirements.init_table()
        self.annotations.init_table()