import sqlite3
from typing import Union

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

    def get_table_names(self):
        """
        Returns a list of all user-defined tables in the database.

        :return: List[str] - table names
        """
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables

    @property
    def get_db_full_info(self):
        """
        Returns table information:
          - row_count: number of records in the table
          - columns: list of dicts as in get_extended_table_info (name, type, non-NULL count, typeof distribution)

        :return: dict
        """
        db_tables_info = {}
        table_names = self.get_table_names()
        for table_name in table_names:
            row_count = self.count_all_entries_in_table(table_name)
            db_tables_info.update(
                {
                    table_name: row_count,
                }
            )
        return db_tables_info

    def count_all_entries_in_table(self, table: str) -> int:
        count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return count

    def count_notnull_entries_in_table(
        self, column: str, table: str
    ) -> Union[int, None]:
        if self.has_column(column, table):
            count = self.conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} IS NOT NULL"
            ).fetchone()[0]
            return count
        return None

    def has_column(self, column_name: str, table_name: str) -> bool:
        """
        Returns True if the table has a column, otherwise False.

        :param column_name: name of the column
        :param table_name: name of the table
        :return: bool
        """
        cursor = self.conn.execute(f'PRAGMA table_info("{table_name}")')
        columns = [row[1] for row in cursor.fetchall()]  # row[1] is the column name
        cursor.close()
        return column_name in columns
