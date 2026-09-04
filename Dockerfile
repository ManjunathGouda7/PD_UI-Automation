FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    HEADLESS=true \
    APP_ENV=ci

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

COPY . .

CMD ["pytest", "-c", "Configurations/pytest.ini", "Scripts/TestCases", "--alluredir=allure-results"]
