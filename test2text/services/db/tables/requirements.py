from typing import Optional

from .abstract_table import AbstractTable
from sqlite3 import Connection
from sqlite_vec import serialize_float32
from string import Template


class RequirementsTable(AbstractTable):
    """
    This class represents the requirements for test cases in the database.
    """

    def __init__(self, connection: Connection, embedding_size: int):
        super().__init__(connection)
        self.embedding_size = embedding_size

    def init_table(self) -> None:
        """
        Creates the Requirements table in the database if it does not already exist.
        """
        self.connection.execute(
            Template("""
            CREATE TABLE IF NOT EXISTS Requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT ,
                external_id TEXT UNIQUE,
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

    def insert(
        self, summary: str, embedding: list[float] = None, external_id: str = None
    ) -> Optional[int]:
        """
        Inserts a new requirement into the database. If the requirement already exists, it updates the existing record.
        :param summary: The summary of the requirement
        :param embedding: The embedding of the requirement (optional)
        :param external_id: The external ID of the requirement (optional)
        :return: The ID of the inserted or updated requirement, or None if the requirement already exists and was updated.
        """
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO Requirements (summary, embedding, external_id)
            VALUES (?, ?, ?)
            RETURNING id
            """,
            (
                summary,
                serialize_float32(embedding) if embedding is not None else None,
                external_id,
            ),
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    @property
    def count(self) -> int:
        """
        Returns the number of entries in the Requirements table.
        :return: int - the number of entries in the table.
        """
        cursor = self.connection.execute("SELECT COUNT(*) FROM Requirements")
        return cursor.fetchone()[0]

    def get_by_id_raw(
        self, req_id: int
    ) -> Optional[tuple[int, str, str, Optional[bytes]]]:
        """
        Retrieves a requirement by its ID.
        :param req_id: The ID of the requirement to retrieve.
        :return: A tuple containing the requirement's ID, external ID, summary, and embedding, or None if not found.
        """
        cursor = self.connection.execute(
            """
            SELECT id, external_id, summary, embedding
            FROM Requirements
            WHERE id = ?
            """,
            (req_id,),
        )
        return cursor.fetchone()
