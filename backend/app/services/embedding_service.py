import httpx
from app.core.config import settings

HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

_local_model = None


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _local_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if settings.ENVIRONMENT == "production":
        return _embed_via_hf_api(texts)
    model = _get_local_model()
    embeddings = model.encode(texts, batch_size=4, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def _embed_via_hf_api(texts: list[str]) -> list[list[float]]:
    headers = {}
    if settings.HF_TOKEN:
        headers["Authorization"] = f"Bearer {settings.HF_TOKEN}"
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            HF_API_URL,
            json={"inputs": texts, "options": {"wait_for_model": True}},
            headers=headers,
        )
        response.raise_for_status()
    result = response.json()
    embeddings = []
    for item in result:
        if isinstance(item[0], list):
            vec = [sum(x[i] for x in item) / len(item) for i in range(len(item[0]))]
        else:
            vec = item
        embeddings.append(vec)
    return embeddings


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
