import sqlite3
from .abstract_table import AbstractTable


class AnnotationsToRequirementsTable(AbstractTable):
    def init_table(self):
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

    def recreate_table(self):
        self.connection.execute("""
            DROP TABLE IF EXISTS AnnotationsToRequirements
        """)
        self.init_table()

    def insert(
        self, annotation_id: int, requirement_id: int, cached_distance: float
    ) -> bool:
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

    def count(self) -> int:
        cursor = self.connection.execute(
            "SELECT COUNT(*) FROM AnnotationsToRequirements"
        )
        return cursor.fetchone()[0]
