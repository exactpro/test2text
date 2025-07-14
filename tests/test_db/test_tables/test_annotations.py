from unittest import TestCase
from test2text.db.client import DbClient


class TestAnnotationsTable(TestCase):
    def setUp(self):
        self.db = DbClient(":memory:")

    def test_insert_single(self):
        id1 = self.db.annotations.insert("Test Summary 1")
        self.assertIsNotNone(id1)

    def test_insert_multiple(self):
        id1 = self.db.annotations.insert("Test Summary 1")
        id2 = self.db.annotations.insert("Test Summary 2")
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        self.assertNotEqual(id1, id2)

    def test_insert_duplicate(self):
        id1 = self.db.annotations.insert("Test Summary 2")
        id2 = self.db.annotations.insert("Test Summary 2")
        self.assertIsNotNone(id1)
        self.assertIsNone(id2)

    def test_insert_embedding(self):
        embedding = [0.1] * self.db.annotations.embedding_size
        id1 = self.db.annotations.insert("Test Summary 3", embedding)
        self.assertIsNotNone(id1)

    def test_insert_short_embedding(self):
        short_embedding = [0.1] * (self.db.annotations.embedding_size - 1)
        id1 = self.db.annotations.insert("Test Summary 4", short_embedding)
        self.assertIsNone(id1)

    def test_insert_long_embedding(self):
        long_embedding = [0.1] * (self.db.annotations.embedding_size + 1)
        id1 = self.db.annotations.insert("Test Summary 5", long_embedding)
        self.assertIsNone(id1)

    def test_get_or_insert_single(self):
        id1 = self.db.annotations.get_or_insert("Test Summary 6")
        self.assertIsNotNone(id1)

    def test_get_or_insert_multiple(self):
        id1 = self.db.annotations.get_or_insert("Test Summary 7")
        id2 = self.db.annotations.get_or_insert("Test Summary 8")
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        self.assertNotEqual(id1, id2)

    def test_get_or_insert_duplicate(self):
        id1 = self.db.annotations.get_or_insert("Test Summary 9")
        id2 = self.db.annotations.get_or_insert("Test Summary 9")
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        self.assertEqual(id1, id2)
