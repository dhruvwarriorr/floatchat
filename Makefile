PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

.PHONY: setup dev-web dev-api check check-web check-api container clean-generated

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e "./backend[dev,data]"
	npm --prefix frontend ci

dev-web:
	npm --prefix frontend run dev

dev-api:
	$(VENV)/bin/uvicorn app.main:app --app-dir backend --reload --reload-dir backend --host 0.0.0.0 --port 8000

check: check-web check-api

check-web:
	npm --prefix frontend run lint
	npm --prefix frontend test

check-api:
	$(VENV)/bin/ruff check backend scripts
	$(VENV)/bin/pytest backend/tests

container:
	docker build -f deploy/Dockerfile -t floatchat-lite:local .

clean-generated:
	rm -rf frontend/dist
