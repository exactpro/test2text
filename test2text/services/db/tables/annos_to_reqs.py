import sqlite3
from .abstract_table import AbstractTable


class AnnotationsToRequirementsTable(AbstractTable):
    """
    This class represents the relationship between annotations and requirements in the database by closest distance between them.
    """

    def init_table(self) -> None:
        """
        Creates the AnnotationsToRequirements table in the database if it does not already exist.
        """
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS AnnotationsToRequirements (
                annotation_id INTEGER NOT NULL,
                requirement_id INTEGER NOT NULL,
                cached_distance REAL NOT NULL,
                UNIQUE (annotation_id, requirement_id),
                FOREIGN KEY (annotation_id) REFERENCES Annotations(id),
                FOREIGN KEY (requirement_id) REFERENCES Requirements(id)
            )
        """)

    def recreate_table(self) -> None:
        """
        Drops the AnnotationsToRequirements table if it exists and recreates it.
        """
        self.connection.execute("""
            DROP TABLE IF EXISTS AnnotationsToRequirements
        """)
        self.init_table()

    def insert(
        self, annotation_id: int, requirement_id: int, cached_distance: float
    ) -> bool:
        """
        Inserts a new entry into the AnnotationsToRequirements table.
        :param annotation_id: The ID of the annotation
        :param requirement_id: The ID of the requirement
        :param cached_distance: The cached distance between the annotation and the requirement
        :return: True if the insertion was successful, False otherwise.
        """
        try:
            cursor = self.connection.execute(
                """
                INSERT OR IGNORE INTO AnnotationsToRequirements (annotation_id, requirement_id, cached_distance)
                VALUES (?, ?, ?)
                RETURNING true
                """,
                (annotation_id, requirement_id, cached_distance),
            )
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result[0]
        except sqlite3.IntegrityError:
            # If the insert fails due to a duplicate, we simply ignore it
            pass
        return False

    @property
    def count(self) -> int:
        """
        Returns the number of entries in the AnnotationsToRequirements table.
        :return: int - the number of entries in the table.
        """
        cursor = self.connection.execute(
            "SELECT COUNT(*) FROM AnnotationsToRequirements"
        )
        return cursor.fetchone()[0]
