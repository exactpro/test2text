from unittest import TestCase
import logging
logging.basicConfig(level=logging.DEBUG)
SKIP_TESTS = False
try:
    from test2text.embeddings.embed import embed_requirement
except ImportError:
    SKIP_TESTS = True
    def embed_requirement(requirement):
        raise ImportError("Embedding model not available in this environment.")

logger = logging.getLogger()

class TestEmbeddings(TestCase):
    def test_embed_requirement(self):
        if SKIP_TESTS:
            self.skipTest("Skipping tests due to missing model in CI environment.")
        requirement = "The system shall allow users to search for documents."
        logger.debug('Start embedding')
        embedding = embed_requirement(requirement)
        logger.debug('End embedding')
        self.assertEqual(embedding.shape, (768,))