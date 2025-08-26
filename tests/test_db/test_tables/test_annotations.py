from unittest import TestCase
from test2text.services.db.client import DbClient
from test2text.services.utils.sqlite_vec import unpack_float32


def round_vector(vector: list[float]) -> list[float]:
    return [round(x, 6) for x in vector]


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

    def test_set_embedding(self):
        id1 = self.db.annotations.insert("Test Summary 10")
        with self.subTest("Set new embedding"):
            orig_embedding = [0.1] * self.db.annotations.embedding_size
            self.db.annotations.set_embedding(id1, orig_embedding)
            self.db.conn.commit()
            result = self.db.get_embeddings_by_id(id1, "Annotations")
            self.assertIsNotNone(result)
            read_embedding = unpack_float32(result[0])
            self.assertEqual(len(read_embedding), self.db.annotations.embedding_size)
            self.assertEqual(round_vector(read_embedding), round_vector(orig_embedding))
        with self.subTest("Overwrite embedding"):
            new_embedding = [0.9] * self.db.annotations.embedding_size
            self.db.annotations.set_embedding(id1, new_embedding)
            self.db.conn.commit()
            result = self.db.get_embeddings_by_id(id1, "Annotations")
            self.assertIsNotNone(result)
            read_embedding = unpack_float32(result[0])
            self.assertEqual(len(read_embedding), self.db.annotations.embedding_size)
            self.assertEqual(round_vector(read_embedding), round_vector(new_embedding))

    def test_count(self):
        count_before = self.db.annotations.count
        self.db.annotations.insert("Test Summary 11")
        count_after = self.db.annotations.count
        self.assertEqual(count_after, count_before + 1)
