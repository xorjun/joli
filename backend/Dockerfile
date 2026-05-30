FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-core libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py config.py database.py models.py schemas.py auth.py __init__.py backend/
COPY routers/ backend/routers/
COPY services/ backend/services/
COPY static/ backend/static/

RUN mkdir -p outputs/photos outputs/zeugnisse

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
