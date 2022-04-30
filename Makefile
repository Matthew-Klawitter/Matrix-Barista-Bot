run:
	.venv/bin/python src/main.py

install: .venv
	.venv/bin/python -m pip install -r requirements.txt

.venv:
	python3 -m venv .venv

build:
	docker build . -t matrix_bot

start:
	docker-compose up -d

stop:
	docker-compose down
