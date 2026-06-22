#!/bin/bash
celery -A app.workers.celery_app worker --loglevel=info --pool=threads --concurrency=2 &
uvicorn app.main:app --host 0.0.0.0 --port 8000
