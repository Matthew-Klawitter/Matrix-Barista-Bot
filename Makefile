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

init_db_config:
	. venv/bin/activate; cd src; aerich init -t database.TORTOISE_ORM

init_db:
	. venv/bin/activate; cd src; aerich init-db

db_add_migration:
	. venv/bin/activate; cd src; aerich migrate --name $(tag)

db_upgrade:
	. venv/bin/activate; cd src; aerich upgrade

db_downgrade:
	. venv/bin/activate; cd src; aerich downgrade

db_downgrade_to:
	. venv/bin/activate; cd src; aerich downgrade $(version)

db_migration_history:
	. venv/bin/activate; cd src; .venv/bin/python aerich history