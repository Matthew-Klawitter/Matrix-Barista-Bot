run:
	.venv/bin/python src/main.py

install: .venv olm
	cd olm; cmake --build build; cd ..
	cd olm/python; make olm-python3; cd ..
	.venv/bin/python -m pip install -r requirements.txt

.venv:
	python3 -m venv .venv

olm:
	git clone https://gitlab.matrix.org/matrix-org/olm.git
