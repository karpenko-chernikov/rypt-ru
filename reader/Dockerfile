FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TG_DB_PATH=/data/reader.db \
    TG_MEDIA_DIR=/data/media

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./reader

RUN useradd --create-home --uid 10001 reader \
    && mkdir -p /data/media \
    && chown -R reader:reader /data

USER reader

EXPOSE 8000

CMD ["uvicorn", "reader.main:app", "--host", "0.0.0.0", "--port", "8000"]
