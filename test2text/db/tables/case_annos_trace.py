from .abstract_table import AbstractTable

class TestCaseToAnnotationsTable(AbstractTable):
    def init_table(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS CaseAnnosTrace (
                case_id INTEGER NOT NULL,
                annotations TEXT UNIQUE NOT NULL,
                UNIQUE (case_id),
                FOREIGN KEY (case_id) REFERENCES TestCases(id)
            )
        """)

    def insert(self, case_id: int, annotations: str):
        self.connection.execute(
            """
            INSERT OR IGNORE INTO CaseAnnosTrace (case_id, annotations)
            VALUES (?, ?)
            """,
            (case_id, annotations)
        )

    def update_annotations(self, case_id: int, addition: str, delimiter=", "):
        self.connection.execute(
            """
            UPDATE CaseAnnosTrace
            SET annotations = annotations || ? || ?
            WHERE case_id = ?
            """,
            (delimiter, addition, case_id)
        )

    def select_and_concatenate_annos_by_test_case(self):
        test_case_annos = self.connection.execute("""
                                            SELECT c.case_id, GROUP_CONCAT(a.summary, ", ")
                                            FROM CasesAnnosTrace as c
                                            JOIN Annotations as a ON c.annotation_id == a.id
                                            GROUP BY case_id;
                                            """,
                                            )
        return test_case_annos


