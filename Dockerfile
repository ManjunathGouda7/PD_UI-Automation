# Image tag must match the `playwright` version pinned in requirements.txt.
FROM mcr.microsoft.com/playwright/python:v1.62.0-noble

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HEADLESS=true \
    APP_ENV=ci

COPY requirements.txt .
# Browsers are preinstalled in the base image; PyQt6 (desktop GUI) is not needed in CI.
RUN grep -v '^PyQt6' requirements.txt > /tmp/req.txt && \
    pip install --no-cache-dir -r /tmp/req.txt

COPY . .

# Read-only smoke by default; override CMD for other profiles (see README).
CMD ["python", "run.py", "--mode", "smoke", "--allure"]
