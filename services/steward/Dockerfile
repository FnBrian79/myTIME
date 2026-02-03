FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

COPY steward.py .

# Create volume mount point
RUN mkdir -p /data/vault

CMD ["python", "steward.py"]
