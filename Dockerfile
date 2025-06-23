# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt update && apt install -y make curl && apt clean
RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && poetry install --no-root

COPY . .

# Команда запуска
CMD ["make", "run"]