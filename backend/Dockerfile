FROM python:3.11-slim

# Non-root user — never run app code as root
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Whisper cache must be writable by the app user
RUN mkdir -p /home/app/.cache && chown -R app:app /app /home/app/.cache
ENV HOME=/home/app

USER app

EXPOSE 8000

# No --reload in production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
