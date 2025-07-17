from unittest import TestCase
from services.db.client import DbClient


class TestDBClient(TestCase):
    def test_db_client(self):
        db = DbClient(":memory:")
        with self.subTest("extensions"):
            (vec_version,) = db.conn.execute("select vec_version()").fetchone()
            self.assertIsNotNone(vec_version)
