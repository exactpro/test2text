from unittest import TestCase
import logging
logging.basicConfig(level=logging.DEBUG)
from test2text.embeddings.embed import embed_requirement

logger = logging.getLogger()

class TestEmbeddings(TestCase):
    def test_embed_requirement(self):
        requirement = "The system shall allow users to search for documents."
        logger.debug('Start embedding')
        embedding = embed_requirement(requirement)
        logger.debug('End embedding')
        self.assertEqual(embedding.shape, (768,))