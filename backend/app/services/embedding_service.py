import logging
from app.core.config import settings

logger = logging.getLogger(__name__)
_model = None


def _get_model():
    global _model
    if _model is None:
        logger.warning("Loading embedding model from cache...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.EMBEDDING_MODEL, local_files_only=True)
        logger.warning("Embedding model loaded successfully")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    embeddings = model.encode(texts, batch_size=4, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
