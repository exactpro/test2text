from unittest import TestCase
from services.db.client import DbClient


class TestCasesToAnnosTable(TestCase):
    def setUp(self):
        self.db = DbClient(":memory:")
        self.case1 = self.db.test_cases.insert("Test Script 1", "Test Case 1")
        self.case2 = self.db.test_cases.insert("Test Script 1", "Test Case 2")
        self.anno1 = self.db.annotations.insert("Test Annotation 1")
        self.anno2 = self.db.annotations.insert("Test Annotation 2")
        self.wrong_case = 9999
        self.wrong_anno = 8888

    def test_insert_single(self):
        count_before = self.db.cases_to_annos.count()
        inserted = self.db.cases_to_annos.insert(self.case1, self.anno1)
        count_after = self.db.cases_to_annos.count()
        self.assertTrue(inserted)
        self.assertEqual(count_after, count_before + 1)

    def test_insert_multiple(self):
        count_before = self.db.cases_to_annos.count()
        inserted1 = self.db.cases_to_annos.insert(self.case1, self.anno1)
        inserted2 = self.db.cases_to_annos.insert(self.case2, self.anno2)
        count_after = self.db.cases_to_annos.count()
        self.assertTrue(inserted1)
        self.assertTrue(inserted2)
        self.assertEqual(count_after, count_before + 2)

    def test_insert_duplicate(self):
        count_before = self.db.cases_to_annos.count()
        inserted1 = self.db.cases_to_annos.insert(self.case1, self.anno1)
        inserted2 = self.db.cases_to_annos.insert(self.case1, self.anno1)
        count_after = self.db.cases_to_annos.count()
        self.assertTrue(inserted1)
        self.assertFalse(inserted2)  # Second insertion should fail as it's a duplicate
        self.assertEqual(count_after, count_before + 1)

    def test_insert_wrong_case(self):
        count_before = self.db.cases_to_annos.count()
        inserted = self.db.cases_to_annos.insert(self.wrong_case, self.anno1)
        count_after = self.db.cases_to_annos.count()
        self.assertFalse(inserted)  # Should fail due to foreign key constraint
        self.assertEqual(count_after, count_before)

    def test_insert_wrong_annotation(self):
        count_before = self.db.cases_to_annos.count()
        inserted = self.db.cases_to_annos.insert(self.case1, self.wrong_anno)
        count_after = self.db.cases_to_annos.count()
        self.assertFalse(inserted)  # Should fail due to foreign key constraint
        self.assertEqual(count_before, count_after)
