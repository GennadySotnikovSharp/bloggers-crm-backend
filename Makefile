.PHONY: install run

install:
	poetry install

run:
	poetry run uvicorn src.main:app --reload
