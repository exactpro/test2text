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

    def insert(self, case_id: int, annotation_id: int):
        self.connection.execute(
            """
            INSERT OR IGNORE INTO CasesToAnnos (case_id, annotation_id)
            VALUES (?, ?)
            """,
            (case_id, annotation_id)
       )