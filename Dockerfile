# Python 3.11 rather than 3.9: onnxruntime 1.23 requires >= 3.10, so the
# previous base image could not install the pinned wheel at all.
FROM python:3.11-slim

# The app renders Devanagari and reads UTF-8 JSON dictionaries, so the locale
# has to be set before anything touches those files.
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copied first so the dependency layer is cached independently of source edits.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ /app/server/

WORKDIR /app/server

ENV PORT=8080
EXPOSE 8080

# ONE worker, several threads. This is deliberate and load-bearing: list state
# lives in this process's memory (see README "State is ephemeral"), so a second
# worker would put half the sessions in a separate address space and a user
# would see their list vanish and reappear as requests were balanced between
# them. state.Store is thread-safe (RLock), so threads are the safe way to get
# concurrency here. Scaling out would need a shared store first.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 60 app:app"]
