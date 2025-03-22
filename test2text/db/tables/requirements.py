from .abstract_table import AbstractTable
from sqlite3 import Connection
from string import Template


class RequirementsTable(AbstractTable):
    def __init__(self, connection: Connection, embedding_size: int = 512):
        super().__init__(connection)
        self.embedding_size = embedding_size

    def init_table(self):
        self.connection.execute(
            Template("""
            CREATE TABLE IF NOT EXISTS Requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT ,
                external_id TEXT UNIQUE,
                summary TEXT UNIQUE NOT NULL,
                embedding float[$embedding_size],

                CHECK (
                    typeof(embedding) == 'null' or
                    (typeof(embedding) == 'blob' and vec_length(embedding) == $embedding_size)
                )
            )
            """).substitute(embedding_size=self.embedding_size)
        )

    def insert(self, summary: str, embedding: list[float] = None, external_id: str = None) -> int:
        return self.connection.execute(
            """
            INSERT OR IGNORE INTO Annotations (summary, embedding external_id)
            VALUES (?, ?, ?)
            RETURNING id
            """,
            (summary, embedding, external_id)
        ).fetchone()[0]
