import sqlite3
import sqlite_vec

from .tables import RequirementsTable, AnnotationsTable
from ..utils.path import PathParam

class DbClient:
    conn: sqlite3.Connection

    def __init__(self, file_path: PathParam, embedding_dim: int = 768):
        self.conn = sqlite3.connect(file_path)
        self.embedding_dim = embedding_dim
        self._install_extension()
        self._init_tables()

    def _install_extension(self):
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)

    def _init_tables(self):
        self.requirements = RequirementsTable(self.conn, self.embedding_dim)
        self.annotations = AnnotationsTable(self.conn, self.embedding_dim)
        self.requirements.init_table()
        self.annotations.init_table()