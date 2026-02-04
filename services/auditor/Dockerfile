FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY auditor.py crypto_utils.py ./

RUN mkdir -p /data/vault /var/log/gauntlet

CMD ["python", "auditor.py"]
