from test2text.services.utils.semver import Semver
from unittest import TestCase


class TestSemver(TestCase):
    def test_initialization(self):
        version = Semver("1.2.3")
        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 2)
        self.assertEqual(version.patch, 3)

    def test_str(self):
        version = Semver("1.2.3")
        self.assertEqual(str(version), "1.2.3")

    def test_equality(self):
        version1 = Semver("1.2.3")
        version2 = Semver("1.2.3")
        self.assertTrue(version1 == version2)
        self.assertTrue(version1 == "1.2.3")
        self.assertFalse(version1 != version2)

    def test_comparison(self):
        version1 = Semver("1.2.3")
        version2 = Semver("1.2.4")
        self.assertTrue(version1 < version2)
        self.assertTrue(version1 <= version2)
        self.assertTrue(version2 > version1)
        self.assertTrue(version2 >= version1)
