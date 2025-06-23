.PHONY: install run

install:
	poetry install

run:
	PYTHONPATH=./src poetry run uvicorn src.main:app --reload
