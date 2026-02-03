FROM python:3.11-slim

WORKDIR /app

COPY auditor.py .

RUN mkdir -p /data/vault /var/log/gauntlet

CMD ["python", "auditor.py"]
