FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir flask requests

COPY triage.py .

EXPOSE 8080

CMD ["python", "triage.py"]
