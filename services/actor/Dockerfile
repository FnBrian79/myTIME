FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY actor.py hallucination_engine.py personas.yaml requirements.txt* ./

# If requirements.txt doesn't exist yet, we'll install requests and pyyaml directly
RUN pip install --no-cache-dir requests pyyaml

CMD ["python", "actor.py"]
