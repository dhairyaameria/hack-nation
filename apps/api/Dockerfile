# FastAPI — deploy on Render / Railway / Fly (not Vercel: Analyze exceeds serverless timeouts)
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/api /app
COPY shared /shared

EXPOSE 8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
