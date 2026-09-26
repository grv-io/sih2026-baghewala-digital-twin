.PHONY: dev install test build dashboard docker docker-run

VENV_PY := .venv/bin/python
ifeq ($(OS),Windows_NT)
	VENV_PY := .venv/Scripts/python.exe
endif

install:
	$(VENV_PY) -m pip install -r requirements.txt

dev:
	$(VENV_PY) -m uvicorn api.main:app --reload --port 8000

test:
	$(VENV_PY) -m pytest -q

dashboard:
	node dashboard/build.js

docker:
	docker build -t baghewala-digital-twin .

docker-run:
	docker run --rm -p 8000:8000 -v twin-data:/app/data baghewala-digital-twin
