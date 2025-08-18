from unittest import TestCase
from test2text.services.db.client import DbClient


class TestTestCasesTable(TestCase):
    def setUp(self):
        self.db = DbClient(":memory:")

    def test_insert_single(self):
        id1 = self.db.test_cases.insert("Test Script 1", "Test Case 1")
        self.assertIsNotNone(id1)
        self.assertIsInstance(id1, int)

    def test_insert_multiple(self):
        id1 = self.db.test_cases.insert("Test Script 2", "Test Case 2")
        id2 = self.db.test_cases.insert("Test Script 3", "Test Case 3")
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        self.assertNotEqual(id1, id2)

    def test_insert_duplicate(self):
        id1 = self.db.test_cases.insert("Test Script 4", "Test Case 4")
        id2 = self.db.test_cases.insert("Test Script 4", "Test Case 4")
        self.assertIsNotNone(id1)
        self.assertIsNone(id2)

    def test_get_or_insert_single(self):
        id1 = self.db.test_cases.get_or_insert("Test Script 8", "Test Case 8")
        self.assertIsNotNone(id1)
        self.assertIsInstance(id1, int)

    def test_get_or_insert_multiple(self):
        id1 = self.db.test_cases.get_or_insert("Test Script 9", "Test Case 9")
        id2 = self.db.test_cases.get_or_insert("Test Script 10", "Test Case 10")
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        self.assertNotEqual(id1, id2)

    def test_get_or_insert_duplicate(self):
        id1 = self.db.test_cases.get_or_insert("Test Script 11", "Test Case 11")
        id2 = self.db.test_cases.get_or_insert("Test Script 11", "Test Case 11")
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        self.assertEqual(id1, id2)

    def test_insert_embedding(self):
        embedding = [0.1] * self.db.test_cases.embedding_size
        id1 = self.db.test_cases.insert("Test Script 12", "Test Case 12", embedding)
        self.assertIsNotNone(id1)

    def test_insert_short_embedding(self):
        short_embedding = [0.1] * (self.db.test_cases.embedding_size - 1)
        id1 = self.db.test_cases.insert("Test Script 13", "Test Case 13", short_embedding)
        self.assertIsNone(id1)

    def test_insert_long_embedding(self):
        long_embedding = [0.1] * (self.db.test_cases.embedding_size + 1)
        id1 = self.db.test_cases.insert("Test Script 14", "Test Case 14",long_embedding)
        self.assertIsNone(id1)