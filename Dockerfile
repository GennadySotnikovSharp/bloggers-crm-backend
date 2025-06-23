# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
 && poetry install --no-dev --no-interaction --no-ansi

COPY . .

# Команда запуска
CMD ["make", "run"]