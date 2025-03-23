from sentence_transformers import SentenceTransformer
import numpy as np
import logging
logger = logging.getLogger()

logger.debug('Loading model')
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)
logger.debug('Model loaded')

def embed_requirement(requirement: str) -> np.ndarray:
    return model.encode(['search_document: ' + requirement])[0]
