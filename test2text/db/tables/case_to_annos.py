from .abstract_table import AbstractTable

class TestCaseToAnnotationsTable(AbstractTable):
    def init_table(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS CaseToAnnos (
                case_id INTEGER NOT NULL,
                annotations TEXT UNIQUE NOT NULL,
                UNIQUE (case_id),
                FOREIGN KEY (case_id) REFERENCES TestCases(id)
            )
        """)

    def insert(self, case_id: int, annotations: str):
        self.connection.execute(
            """
            INSERT OR IGNORE INTO CaseToAnnos (case_id, annotations)
            VALUES (?, ?)
            """,
            (case_id, annotations)
       )