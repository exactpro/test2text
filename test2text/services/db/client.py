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

    def get_table_names(self) -> list[str]:
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

    def get_column_values(self, *columns: str, from_table: str) -> list[tuple]:
        """
        Returns the values of the specified columns from the specified table.
        :param columns: list of column names
        :param from_table: name of the table
        :return: list of tuples containing the values of the specified columns
        """
        cursor = self.conn.execute(f"SELECT {', '.join(columns)} FROM {from_table}")
        return cursor.fetchall()

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
            row_count = self.count_all_entries(table_name)
            db_tables_info.update(
                {
                    table_name: row_count,
                }
            )
        return db_tables_info

    def count_all_entries(self, from_table: str) -> int:
        count = self.conn.execute(f"SELECT COUNT(*) FROM {from_table}").fetchone()[0]
        return count

    def count_notnull_entries(self, *columns: str, from_table: str) -> int:
        """
        Count the number of non-null entries in the specified columns of the specified table.
        :param columns: list of column names
        :param from_table: name of the table
        """
        count = self.conn.execute(
            f"SELECT COUNT(*) FROM {from_table} WHERE {' AND  '.join([column + ' IS NOT NULL' for column in columns])}"
        ).fetchone()[0]
        return count

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

    def get_null_entries(self, from_table: str) -> list:
        """
        Returns values (id and summary) witch has  null values in its embedding column.
        """
        cursor = self.conn.execute(
            f"SELECT id, summary FROM {from_table} WHERE embedding IS NULL"
        )
        return cursor.fetchall()

    def get_distances(self) -> list[tuple[int, int, float]]:
        """
        Returns a list of tuples containing the id of the annotation and the id of the requirement,
        and the distance between their embeddings (anno_id, req_id, distance).
        The distance is calculated using the L2 norm. The results are ordered by requirement ID and distance.
        """
        cursor = self.conn.execute("""
                SELECT 
                    Annotations.id AS anno_id,
                    Requirements.id AS req_id,
                    vec_distance_L2(Annotations.embedding, Requirements.embedding) AS distance
                FROM Annotations, Requirements
                WHERE Annotations.embedding IS NOT NULL AND Requirements.embedding IS NOT NULL
                ORDER BY req_id, distance
                """)
        return cursor.fetchall()

    def get_embeddings_from_annotations_to_requirements_table(self):
        """
        Returns a list of annotation's embeddings that are stored in the AnnotationsToRequirements table.
        The embeddings are ordered by annotation ID.
        """
        cursor = self.conn.execute("""
            SELECT embedding FROM Annotations
            WHERE id IN (
            SELECT DISTINCT annotation_id FROM AnnotationsToRequirements
            )
            """)
        return cursor.fetchall()

    def join_all_tables_by_requirements(
        self, where_clauses="", params=None
    ) -> list[tuple]:
        """
        Extract values from requirements with related annotations and their test cases based on the provided where clauses and parameters.
        Return a list of tuples containing :
            req_id,
            req_external_id,
            req_summary,
            req_embedding,
            anno_id,
            anno_summary,
            anno_embedding,
            distance,
            case_id,
            test_script,
            test_case
        """
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        sql = f"""
                            SELECT
                                Requirements.id as req_id,
                                Requirements.external_id as req_external_id,
                                Requirements.summary as req_summary,
                                Requirements.embedding as req_embedding,

                                Annotations.id as anno_id,
                                Annotations.summary as anno_summary,
                                Annotations.embedding as anno_embedding,

                                AnnotationsToRequirements.cached_distance as distance,

                                TestCases.id as case_id,
                                TestCases.test_script as test_script,
                                TestCases.test_case as test_case
                            FROM
                                Requirements
                                    JOIN AnnotationsToRequirements ON Requirements.id = AnnotationsToRequirements.requirement_id
                                    JOIN Annotations ON Annotations.id = AnnotationsToRequirements.annotation_id
                                    JOIN CasesToAnnos ON Annotations.id = CasesToAnnos.annotation_id
                                    JOIN TestCases ON TestCases.id = CasesToAnnos.case_id
                            {where_sql}
                            ORDER BY
                                Requirements.id, AnnotationsToRequirements.cached_distance, TestCases.id
                            LIMIT ?
                """
        data = self.conn.execute(sql, params)
        return data.fetchall()

    def get_ordered_values_from_test_cases(
        self, distance_sql="", where_clauses="", distance_order_sql="", params=None
    ) -> list[tuple]:
        """
        Extracted values from TestCases table based on the provided where clauses and specified parameters ordered by distance and id.
        Return a list of tuples containing :
            case_id,
            test_script,
            test_case,
            distance between test case and typed by user text embeddings if it is specified,
        """
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        sql = f"""
                            SELECT
                                TestCases.id as case_id,
                                TestCases.test_script as test_script,
                                TestCases.test_case as test_case
                                {distance_sql}
                            FROM
                                TestCases
                            {where_sql}
                            ORDER BY
                                {distance_order_sql}TestCases.id
                            """
        data = self.conn.execute(sql, params)
        return data.fetchall()

    def join_all_tables_by_test_cases(
        self, where_clauses="", params=None
    ) -> list[tuple]:
        """
        Join all tables related to test cases based on the provided where clauses and specified parameters.
        Return a list of tuples containing :
            case_id,
            test_script,
            test_case,
            anno_id,
            anno_summary,
            anno_embedding,
            distance between annotation and requirement embeddings,
            req_id,
            req_external_id,
            req_summary,
            req_embedding
        """
        where_sql = ""
        if where_clauses:
            where_sql = f"WHERE {' AND '.join(where_clauses)}"

        sql = f"""
                            SELECT
                                TestCases.id as case_id,
                                TestCases.test_script as test_script,
                                TestCases.test_case as test_case,

                                Annotations.id as anno_id,
                                Annotations.summary as anno_summary,
                                Annotations.embedding as anno_embedding,

                                AnnotationsToRequirements.cached_distance as distance,

                                Requirements.id as req_id,
                                Requirements.external_id as req_external_id,
                                Requirements.summary as req_summary,
                                Requirements.embedding as req_embedding
                            FROM
                                TestCases
                                    JOIN CasesToAnnos ON TestCases.id = CasesToAnnos.case_id
                                    JOIN Annotations ON Annotations.id = CasesToAnnos.annotation_id
                                    JOIN AnnotationsToRequirements ON Annotations.id = AnnotationsToRequirements.annotation_id
                                    JOIN Requirements ON Requirements.id = AnnotationsToRequirements.requirement_id
                            {where_sql}
                            ORDER BY
                                case_id, distance, req_id
                            LIMIT ?
                            """
        data = self.conn.execute(sql, params)
        return data.fetchall()

    def get_embeddings_by_id(self, id1: int, from_table: str) -> float:
        """
        Returns the embedding of the specified id from the specified table.
        """
        cursor = self.conn.execute(
            f"SELECT embedding FROM {from_table} WHERE id = ?", (id1,)
        )
        return cursor.fetchone()
