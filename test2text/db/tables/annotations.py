from typing import Optional

from .abstract_table import AbstractTable
from sqlite3 import Connection
from sqlite_vec import serialize_float32
from string import Template


class AnnotationsTable(AbstractTable):
    def __init__(self, connection: Connection, embedding_size: int):
        super().__init__(connection)
        self.embedding_size = embedding_size


    def init_table(self):
        self.connection.execute(
            Template("""
            CREATE TABLE IF NOT EXISTS Annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT ,
                summary TEXT UNIQUE NOT NULL,
                embedding float[$embedding_size],
                
                CHECK (
                    typeof(embedding) == 'null' or
                    (typeof(embedding) == 'blob' and vec_length(embedding) == $embedding_size)
                )
            )
            """).substitute(embedding_size=self.embedding_size)
        )

    def insert(self, summary: str, embedding: list[float] = None) -> Optional[int]:
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO Annotations (summary, embedding)
            VALUES (?, ?)
            RETURNING id
            """,
            (summary, serialize_float32(embedding) if embedding else None)
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
