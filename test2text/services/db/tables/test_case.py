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
