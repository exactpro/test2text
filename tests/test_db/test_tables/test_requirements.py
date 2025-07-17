from unittest import TestCase
from services.db.client import DbClient


class TestRequirementsTable(TestCase):
    def setUp(self):
        self.db = DbClient(":memory:")

    def test_insert_single(self):
        id1 = self.db.requirements.insert("Test Requirement 1")
        self.assertIsNotNone(id1)

    def test_insert_multiple(self):
        id1 = self.db.requirements.insert("Test Requirement 2")
        id2 = self.db.requirements.insert("Test Requirement 3")
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        self.assertNotEqual(id1, id2)

    def test_insert_duplicate(self):
        id1 = self.db.requirements.insert("Test Requirement 4")
        id2 = self.db.requirements.insert("Test Requirement 4")
        self.assertIsNotNone(id1)
        self.assertIsNone(id2)

    def test_insert_with_external_id_single(self):
        id1 = self.db.requirements.insert("Test Requirement 1", external_id="ext-1")
        self.assertIsNotNone(id1)

    def test_insert_with_external_id_multiple(self):
        id1 = self.db.requirements.insert("Test Requirement 2", external_id="ext-2")
        id2 = self.db.requirements.insert("Test Requirement 3", external_id="ext-3")
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        self.assertNotEqual(id1, id2)

    def test_insert_with_external_id_duplicate(self):
        id1 = self.db.requirements.insert("Test Requirement 4", external_id="ext-4")
        id2 = self.db.requirements.insert("Test Requirement 4", external_id="ext-4")
        self.assertIsNotNone(id1)
        self.assertIsNone(id2)

    def test_insert_duplicate_external_id(self):
        id1 = self.db.requirements.insert("Test Requirement 2", external_id="ext-2")
        id2 = self.db.requirements.insert("Test Requirement 3", external_id="ext-2")
        self.assertIsNotNone(id1)
        self.assertIsNone(id2)
