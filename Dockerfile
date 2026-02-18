# Use official Python image
FROM python:3.11-slim

# Set environment variables (New & Important)
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files (useless in containers)
# PYTHONUNBUFFERED: Ensures logs are flushed immediately to the terminal (crucial for debugging)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (New - Optional but likely needed for Postgres)
# libpq-dev and gcc are often required to build psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- CACHE OPTIMIZATION START ---
# 1. Copy ONLY the dependency files first
COPY pyproject.toml poetry.lock ./

# 2. Install Poetry and dependencies
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main

# 3. NOW copy the rest of your application code
COPY . .
# --- CACHE OPTIMIZATION END ---

# Expose API port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]