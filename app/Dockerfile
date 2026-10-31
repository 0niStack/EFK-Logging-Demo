FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY app.py .

RUN useradd -r -u 10001 appuser
USER appuser

CMD ["python", "app.py"]
