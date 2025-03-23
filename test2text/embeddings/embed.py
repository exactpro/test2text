from sentence_transformers import SentenceTransformer
import numpy as np
import logging
logger = logging.getLogger()

logger.debug('Loading model')
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)
logger.debug('Model loaded')

def embed_requirement(requirement: str) -> np.ndarray:
    return model.encode(['search_document: ' + requirement])[0]

def embed_requirements_batch(requirements: list[str]) -> np.ndarray:
    return model.encode(['search_document: ' + requirement for requirement in requirements])

def embed_annotation(annotation: str) -> np.ndarray:
    return model.encode(['search_query: ' + annotation])[0]

def embed_annotations_batch(annotations: list[str]) -> np.ndarray:
    return model.encode(['search_query: ' + annotation for annotation in annotations])
