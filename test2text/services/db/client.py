import sqlite3
import sqlite_vec
import logging

from test2text.services.utils.semver import Semver
from .tables import (
    RequirementsTable,
    AnnotationsTable,
    AnnotationsToRequirementsTable,
    TestCasesTable,
    TestCasesToAnnotationsTable,
)
from ..utils.path import PathParam

logger = logging.getLogger(__name__)


class DbClient:
    conn: sqlite3.Connection

    @staticmethod
    def _check_sqlite_version():
        # Version when RETURNED is available
        REQUIRED_SQLITE_VERSION = Semver("3.35.0")
        sqlite_version = Semver(sqlite3.sqlite_version)
        if sqlite_version < REQUIRED_SQLITE_VERSION:
            raise RuntimeError(
                f"SQLite version {sqlite_version} is too old. "
                f"Required version is {REQUIRED_SQLITE_VERSION}. "
                "Please upgrade SQLite in your system to use test2text."
            )

    def __init__(self, file_path: PathParam, embedding_dim: int = 768):
        self._check_sqlite_version()
        logger.info("Connecting to database at %s", file_path)
        self.conn = sqlite3.connect(file_path)
        self.embedding_dim = embedding_dim
        self._turn_on_foreign_keys()
        self._install_extension()
        self._init_tables()
        logger.info("Connected to database at %s", file_path)

    def _install_extension(self):
        self.conn.enable_load_extension(True)
        logger.debug("Installing sqlite_vec extension")
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)

    def _turn_on_foreign_keys(self):
        self.conn.execute("PRAGMA foreign_keys = ON")
        logger.debug("Foreign keys enabled")

    def _init_tables(self):
        self.requirements = RequirementsTable(self.conn, self.embedding_dim)
        self.annotations = AnnotationsTable(self.conn, self.embedding_dim)
        self.test_cases = TestCasesTable(self.conn, self.embedding_dim)
        self.annos_to_reqs = AnnotationsToRequirementsTable(self.conn)
        self.cases_to_annos = TestCasesToAnnotationsTable(self.conn)
        self.requirements.init_table()
        self.annotations.init_table()
        self.test_cases.init_table()
        self.annos_to_reqs.init_table()
        self.cases_to_annos.init_table()

    def close(self):
        # Supposedly, uncommited changes block changes from other connections
        self.conn.commit()
        self.conn.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __enter__(self):
        return self