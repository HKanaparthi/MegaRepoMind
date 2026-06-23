FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/repos && useradd -m appuser && chown -R appuser /tmp/repos

# Pre-download the embedding model and create a readable token file
# so huggingface_hub doesn't fail at runtime looking for credentials
RUN mkdir -p /root/.cache/huggingface \
    && touch /root/.cache/huggingface/token \
    && chmod 644 /root/.cache/huggingface/token

# Pre-download the embedding model so it's baked into the image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
