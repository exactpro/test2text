from unittest import TestCase
from test2text.db.client import DbClient

class TestDBClient(TestCase):
    def test_db_client(self):
        db = DbClient(':memory:')
        with self.subTest('extensions'):
            vec_version, = db.conn.execute("select vec_version()").fetchone()
            self.assertIsNotNone(vec_version)
        with self.subTest(table='annotations'):
            with self.subTest('insert 2 different summaries'):
                id1 = db.annotations.get_or_insert('Summary 1')
                id2 = db.annotations.get_or_insert('Summary 2')
                self.assertEqual(id1, 1)
                self.assertEqual(id2, 2)
            with self.subTest('insert 2 same summaries'):
                id3 = db.annotations.get_or_insert('Summary 1')
                id4 = db.annotations.get_or_insert('Summary 2')
                self.assertIsNone(id3)
                self.assertIsNone(id4)
            with self.subTest('embedding of different size'):
                id5 = db.annotations.get_or_insert('Summary 3', [1., 2., 3.])
                self.assertIsNone(id5)
            with self.subTest('insert summary with embedding'):
                id6 = db.annotations.get_or_insert('Summary 3', [1.0] * db.annotations.embedding_size)
                self.assertEqual(id6, 6)