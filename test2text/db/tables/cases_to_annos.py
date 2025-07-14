import sqlite3

from .abstract_table import AbstractTable

class TestCasesToAnnotationsTable(AbstractTable):
    def init_table(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS CasesToAnnos (
                case_id INTEGER NOT NULL,
                annotation_id INTEGER NOT NULL,
                UNIQUE (case_id, annotation_id),
                FOREIGN KEY (case_id) REFERENCES TestCases(id),
                FOREIGN KEY (annotation_id) REFERENCES Annotations(id)
            )
        """)

    def recreate_table(self):
        self.connection.execute("""
            DROP TABLE IF EXISTS CasesToAnnos
        """)
        self.init_table()

    def insert(self, case_id: int, annotation_id: int):
        try:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO CasesToAnnos (case_id, annotation_id)
                VALUES (?, ?)
                """,
                (case_id, annotation_id)
           )
        except sqlite3.IntegrityError:
            # If the insert fails due to a duplicate, we simply ignore it
            pass

    def count(self) -> int:
        cursor = self.connection.execute("SELECT COUNT(*) FROM CasesToAnnos")
        return cursor.fetchone()[0]