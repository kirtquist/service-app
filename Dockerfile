FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install .

# Cloud Run sets PORT (typically 8080). Local default in main.py is 8090.
CMD ["service-app-api"]
