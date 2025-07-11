from .abstract_table import AbstractTable

class TestCasesTable(AbstractTable):
    def init_table(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS TestCases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_script TEXT NOT NULL,
                test_case TEXT NOT NULL,
                UNIQUE (test_script, test_case)
            )
        """)

    def insert(self, test_script: str, test_case: str):
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO TestCases (test_script, test_case)
            VALUES (?, ?)
            """,
            (test_script, test_case)
        )
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result[0]
        else:
            cursor = self.connection.execute(
                """
                SELECT id FROM TestCases
                WHERE test_script = ? AND test_case = ?
                """,
                (test_script, test_case)
            )
            result = cursor.fetchone()
            cursor.close()
            return result[0]