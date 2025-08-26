from unittest import TestCase
from test2text.services.db.client import DbClient


class TestAnnosToReqsTable(TestCase):
    def setUp(self):
        self.db = DbClient(":memory:")
        self.anno1 = self.db.annotations.insert("Test Annotation 1")
        self.anno2 = self.db.annotations.insert("Test Annotation 2")
        self.req1 = self.db.requirements.insert("Test Requirement 1")
        self.req2 = self.db.requirements.insert("Test Requirement 2")
        self.wrong_anno = 9999
        self.wrong_req = 8888

    def test_insert_single(self):
        count_before = self.db.annos_to_reqs.count
        inserted = self.db.annos_to_reqs.insert(self.anno1, self.req1, 1)
        count_after = self.db.annos_to_reqs.count
        self.assertTrue(inserted)
        self.assertEqual(count_after, count_before + 1)

    def test_insert_multiple(self):
        count_before = self.db.annos_to_reqs.count
        inserted1 = self.db.annos_to_reqs.insert(self.anno1, self.req1, 1)
        inserted2 = self.db.annos_to_reqs.insert(self.anno2, self.req2, 1)
        count_after = self.db.annos_to_reqs.count
        self.assertTrue(inserted1)
        self.assertTrue(inserted2)
        self.assertEqual(count_after, count_before + 2)

    def test_insert_duplicate(self):
        count_before = self.db.annos_to_reqs.count
        inserted1 = self.db.annos_to_reqs.insert(self.anno1, self.req1, 1)
        inserted2 = self.db.annos_to_reqs.insert(self.anno1, self.req1, 1)
        count_after = self.db.annos_to_reqs.count
        self.assertTrue(inserted1)
        self.assertFalse(inserted2)  # Second insertion should fail as it's a duplicate
        self.assertEqual(count_after, count_before + 1)

    def test_insert_wrong_annotation(self):
        count_before = self.db.annos_to_reqs.count
        inserted = self.db.annos_to_reqs.insert(self.wrong_anno, self.req1, 1)
        count_after = self.db.annos_to_reqs.count
        self.assertFalse(inserted)  # Should fail due to foreign key constraint
        self.assertEqual(count_after, count_before)

    def test_insert_wrong_requirement(self):
        count_before = self.db.annos_to_reqs.count
        inserted = self.db.annos_to_reqs.insert(self.anno1, self.wrong_req, 1)
        count_after = self.db.annos_to_reqs.count
        self.assertFalse(inserted)  # Should fail due to foreign key constraint
        self.assertEqual(count_before, count_after)

    def test_count(self):
        count_before = self.db.annos_to_reqs.count
        self.db.annos_to_reqs.insert(self.anno1, self.req1, 1)
        self.db.annos_to_reqs.insert(self.anno2, self.req2, 1)
        count_after = self.db.annos_to_reqs.count
        self.assertEqual(count_after, count_before + 2)
