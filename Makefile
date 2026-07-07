.PHONY: install test lint run docker-build docker-up

install:
	python -m pip install -r requirements-dev.txt

test:
	pytest -q

lint:
	ruff check app tests

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload

docker-build:
	docker build -t hr-screening-bot-python .

docker-up:
	docker compose up --build
