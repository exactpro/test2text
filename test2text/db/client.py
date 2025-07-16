import sqlite3
import sqlite_vec
import logging

from .tables import RequirementsTable, AnnotationsTable, AnnotationsToRequirementsTable, TestCasesTable, TestCasesToAnnotationsTable
from ..utils.path import PathParam

logger = logging.getLogger(__name__)

class DbClient:
    conn: sqlite3.Connection

    def __init__(self, file_path: PathParam, embedding_dim: int = 768):
        logger.info('Connecting to database at %s', file_path)
        self.conn = sqlite3.connect(file_path)
        self.embedding_dim = embedding_dim
        self._install_extension()
        self._init_tables()
        logger.info('Connected to database at %s', file_path)

    def _install_extension(self):
        self.conn.enable_load_extension(True)
        logger.debug('Installing sqlite_vec extension')
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)

    def _init_tables(self):
        self.requirements = RequirementsTable(self.conn, self.embedding_dim)
        self.annotations = AnnotationsTable(self.conn, self.embedding_dim)
        self.test_cases = TestCasesTable(self.conn)
        self.annos_to_reqs = AnnotationsToRequirementsTable(self.conn)
        self.cases_to_annos = TestCasesToAnnotationsTable(self.conn)
        self.requirements.init_table()
        self.annotations.init_table()
        self.test_cases.init_table()
        self.annos_to_reqs.init_table()
        self.cases_to_annos.init_table()