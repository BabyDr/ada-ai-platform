FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

ENV LLM_MODE=mock
EXPOSE 18765

CMD ["python", "-m", "uvicorn", "adaworks.main:app", "--host", "0.0.0.0", "--port", "18765"]
