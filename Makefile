run: credentials.json
	.venv/bin/python src/main.py

credentials.json:
	./create_credentials.sh

install: .venv
	.venv/bin/python -m pip install -r requirements.txt

.venv:
	python3 -m venv .venv

build: credentials.json
	docker build . -t matrix_bot

start:
	docker-compose up -d
