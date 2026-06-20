# MegaRepoMind

**Your AI Engineering Teammate** — Paste any GitHub repository and instantly understand its architecture, APIs, and implementation details through an AI-powered chat interface.

## What It Does

- Paste a GitHub URL → repository gets cloned, parsed, and indexed
- Ask any question about the codebase
- Get precise answers with **file-level citations** (file path + line numbers)
- All backed by a RAG pipeline: embeddings → vector search → Claude AI

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Tailwind CSS, React Query |
| Backend | FastAPI, SQLAlchemy (async) |
| Database | PostgreSQL + pgvector |
| Embeddings | sentence-transformers (BAAI/bge-small-en-v1.5) |
| LLM | Anthropic Claude API |
| Queue | Celery + Redis |
| Deployment | Docker, Railway |

## Quick Start

### Prerequisites
- Docker + Docker Compose
- Anthropic API key (get one at https://console.anthropic.com)

### 1. Clone and configure

```bash
git clone https://github.com/yourusername/megarepomind
cd megarepomind
cp .env.example .env
```

Edit `.env` and add your `ANTHROPIC_API_KEY`.

### 2. Run

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3. Use it

1. Register an account
2. Paste a GitHub repository URL
3. Wait for indexing (30 seconds – 2 minutes depending on repo size)
4. Start chatting with the codebase

## Architecture

```
GitHub URL
    ↓
Clone Repository (git)
    ↓
Parse Files (language-aware)
    ↓
Chunk Code (function/class-aware splitting)
    ↓
Generate Embeddings (sentence-transformers, local, free)
    ↓
Store in pgvector (PostgreSQL)
    ↓
User asks question
    ↓
Embed question → cosine similarity search → top-K chunks
    ↓
Assemble context → Claude API → answer with citations
```

## Deployment on Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add PostgreSQL and Redis plugins
4. Set environment variables (same as `.env`)
5. Deploy — Railway auto-detects Docker

## Project Structure

```
megarepomind/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # FastAPI route handlers
│   │   ├── core/           # Config, security (JWT/bcrypt)
│   │   ├── db/             # SQLAlchemy async engine
│   │   ├── models/         # ORM models (User, Repository, Chunk, Chat)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic (ingestion, RAG, chat)
│   │   └── workers/        # Celery tasks (background indexing)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/          # Login, Dashboard, Repository, Chat
│       ├── components/     # Layout, ChatMessage
│       ├── hooks/          # useAuth
│       └── services/       # API client (axios)
├── docker-compose.yml
└── .env.example
```
