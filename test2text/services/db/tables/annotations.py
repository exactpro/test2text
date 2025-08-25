from typing import Optional

from .abstract_table import AbstractTable
from sqlite3 import Connection
from sqlite_vec import serialize_float32
from string import Template


class AnnotationsTable(AbstractTable):
    """
    This class represents the annotations of test cases in the database.
    """

    def __init__(self, connection: Connection, embedding_size: int):
        super().__init__(connection)
        self.embedding_size = embedding_size

    def init_table(self):
        """
        Creates the Annotations table in the database if it does not already exist.
        """
        self.connection.execute(
            Template("""
            CREATE TABLE IF NOT EXISTS Annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary TEXT UNIQUE NOT NULL,
                embedding float[$embedding_size],
                
                CHECK (
                    typeof(embedding) == 'null' or
                    (typeof(embedding) == 'blob' 
                        and vec_length(embedding) == $embedding_size)
                )
            )
            """).substitute(embedding_size=self.embedding_size)
        )

    def insert(self, summary: str, embedding: list[float] = None) -> Optional[int]:
        """
        Inserts a new annotation into the database. If the annotation already exists, it updates the existing record.
        :param summary: The summary of the annotation
        :param embedding: The embedding of the annotation (optional)
        :return: The ID of the inserted or updated annotation, or None if the annotation already exists and was updated.
        """
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO Annotations (summary, embedding)
            VALUES (?, ?)
            RETURNING id
            """,
            (summary, serialize_float32(embedding) if embedding is not None else None),
        )
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result[0]
        else:
            return None

    def get_or_insert(self, summary: str, embedding: list[float] = None) -> int:
        """
        Inserts a new annotation into the database if it does not already exist, otherwise returns the existing annotation's ID.
        :param summary: The summary of the annotation
        :param embedding: The embedding of the annotation (optional)
        :return: The ID of the inserted or existing annotation.
        """
        inserted_id = self.insert(summary, embedding)
        if inserted_id is not None:
            return inserted_id
        else:
            cursor = self.connection.execute(
                """
                SELECT id FROM Annotations
                WHERE summary = ?
                """,
                (summary,),
            )
            result = cursor.fetchone()
            cursor.close()
            return result[0]

    def set_embedding(self, anno_id: int, embedding: list[float]) -> None:
        """
        Sets the embedding for a given annotation ID.
        :param anno_id: The ID of the annotation
        :param embedding: The new embedding for the annotation
        """
        if len(embedding) != self.embedding_size:
            raise ValueError(
                f"Embedding size must be {self.embedding_size}, got {len(embedding)}"
            )
        serialized_embedding = serialize_float32(embedding)
        self.connection.execute(
            """
            UPDATE Annotations
            SET embedding = ?
            WHERE id = ?
            """,
            (serialized_embedding, anno_id),
        )

    @property
    def count(self) -> int:
        """
        Returns the number of entries in the Annotations table.
        :return: int - the number of entries in the table.
        """
        cursor = self.connection.execute("SELECT COUNT(*) FROM Annotations")
        return cursor.fetchone()[0]
