FROM python:3.12-slim

# ffmpeg powers yt-dlp audio extraction / merges and moviepy trimming
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads trimmed_videos

# Bind all interfaces inside the container; map the port on the host.
ENV HOST=0.0.0.0 \
    PORT=5000 \
    FLASK_DEBUG=0

EXPOSE 5000

# Single process (waitress, multi-threaded) — required so the in-memory job
# registry is shared. Do not scale to multiple replicas.
CMD ["python", "serve.py"]
