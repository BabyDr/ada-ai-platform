# ---- Stage 1: 构建前端 ----
FROM node:20-slim AS frontend

WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ---- Stage 2: 后端 + 前端静态文件 ----
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend /build/dist ./static

ENV LLM_MODE=mock
ENV STATIC_DIR=/app/static

EXPOSE 18765

CMD ["python", "-m", "uvicorn", "adaworks.main:app", "--host", "0.0.0.0", "--port", "18765"]
