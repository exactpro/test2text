from typing import Optional

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

    def insert(self, test_script: str, test_case: str) -> Optional[int]:
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO TestCases (test_script, test_case)
            VALUES (?, ?)
            RETURNING id
            """,
            (test_script, test_case),
        )
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result[0]
        else:
            return None

    def get_or_insert(self, test_script: str, test_case: str) -> int:
        inserted_id = self.insert(test_script, test_case)
        if inserted_id is not None:
            return inserted_id
        else:
            cursor = self.connection.execute(
                """
                SELECT id FROM TestCases
                WHERE test_script = ? AND test_case = ?
                """,
                (test_script, test_case),
            )
            result = cursor.fetchone()
            cursor.close()
            return result[0]
