from string import Template
from typing import Optional
from sqlite_vec import serialize_float32
from sqlite3 import Connection

from .abstract_table import AbstractTable


class TestCasesTable(AbstractTable):
    def __init__(self, connection: Connection, embedding_size: int):
        super().__init__(connection)
        self.embedding_size = embedding_size

    def init_table(self):
        """
        Creates the TestCases table in the database if it does not already exist.
        """
        self.connection.execute(
            Template("""
           
                         CREATE TABLE IF NOT EXISTS TestCases (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            test_script TEXT NOT NULL,
                            test_case TEXT NOT NULL,
                            embedding float[$embedding_size],
                            UNIQUE (test_script, test_case)
                            
                            CHECK (
                                typeof(embedding) == 'null' or
                                (typeof(embedding) == 'blob' 
                                    and vec_length(embedding) == $embedding_size)
                            ) 
                        )
                    """).substitute(embedding_size=self.embedding_size)
        )

    def insert(
        self, test_script: str, test_case: str, embedding: list[float] = None
    ) -> Optional[int]:
        """
        Inserts a new test case into the database. If the test case already exists, it updates the existing record.
        :param test_script: The test script of the test case
        :param test_case: The test case of the test case
        :param embedding: The embedding of the test case (optional)
        :return: The ID of the inserted or updated test case, or None if the test case already exists and was updated.
        """
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO TestCases (test_script, test_case, embedding)
            VALUES (?, ?, ?)
            RETURNING id
            """,
            (
                test_script,
                test_case,
                serialize_float32(embedding) if embedding is not None else None,
            ),
        )
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result[0]
        else:
            return None

    def get_or_insert(self, test_script: str, test_case: str) -> int:
        """
        Inserts a new test case into the database if it does not already exist, otherwise returns the existing test case's ID.
        :param test_script: The test script of the test case
        :param test_case: The test case of the test case
        :return: The ID of the inserted or existing test case.
        """
        inserted_id = self.insert(test_script, test_case)
        if inserted_id is not None:
            return inserted_id
        else:
            cursor = self.connection.execute(
                """
                SELECT id FROM TestCases
                WHERE test_script = ? AND test_case = ?
                """,
                (test_script, test_case),
            )
            result = cursor.fetchone()
            cursor.close()
            return result[0]

    @property
    def count(self) -> int:
        """
        Returns the number of entries in the TestCases table.
        :return: int - the number of entries in the table.
        """
        cursor = self.connection.execute("SELECT COUNT(*) FROM TestCases")
        return cursor.fetchone()[0]

    def get_by_id_raw(
        self, case_id: int
    ) -> Optional[tuple[int, str, str, Optional[bytes]]]:
        """
        Fetches a test case by its ID.
        :param case_id: The ID of the test case to fetch.
        :return: A tuple containing the test case's ID, test script, test case, and embedding (if available), or None if not found.
        """
        cursor = self.connection.execute(
            """
            SELECT id, test_script, test_case, embedding
            FROM TestCases
            WHERE id = ?
            """,
            (case_id,),
        )
        result = cursor.fetchone()
        cursor.close()
        return result
