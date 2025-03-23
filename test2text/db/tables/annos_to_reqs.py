from .abstract_table import AbstractTable

class AnnotationsToRequirementsTable(AbstractTable):
    def init_table(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS AnnotationsToRequirements (
                annotation_id INTEGER NOT NULL,
                requirement_id INTEGER NOT NULL,
                UNIQUE (annotation_id, requirement_id),
                FOREIGN KEY (annotation_id) REFERENCES Annotations(id),
                FOREIGN KEY (requirement_id) REFERENCES Requirements(id)
            )
        """)

    def insert(self, annotation_id: int, requirement_id: int):
        self.connection.execute(
            """
            INSERT OR IGNORE INTO AnnotationsToRequirements (annotation_id, requirement_id)
            VALUES (?, ?)
            """,
            (annotation_id, requirement_id)
        )