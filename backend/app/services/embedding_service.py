from sentence_transformers import SentenceTransformer
from app.core.config import settings
import numpy as np

_model = SentenceTransformer(settings.EMBEDDING_MODEL)


def get_model() -> SentenceTransformer:
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_model()
    embeddings = model.encode(texts, batch_size=4, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
