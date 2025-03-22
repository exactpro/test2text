import sqlite3
import sqlite_vec

from .tables import RequirementsTable, AnnotationsTable

class DbClient:
    conn: sqlite3.Connection

    def __init__(self, file_path: str):
        self.conn = sqlite3.connect(file_path)
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)

        self.requirements = RequirementsTable(self.conn)
        self.annotations = AnnotationsTable(self.conn)
        self.requirements.init_table()
        self.annotations.init_table()