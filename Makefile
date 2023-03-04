py_files := *.py src/*

_: check

.PHONY: build
build:
	python -m pip install --upgrade pip
	python -m pip install --upgrade build
	python -m build

# Pre-commit checks

check: lint check-format check-imports

check-format:
	black --check --diff --color $(py_files) && echo

check-imports:
	isort --check --diff --color $(py_files) && echo

format:
	black $(py_files)

imports:
	isort $(py_files)

lint:
	flake8 $(py_files) && echo

# Installation

pip:
	python -m pip install --upgrade pip

install: install-req
	python -m pip install -e .

install-all: pip
	python -m pip install --upgrade -e . -r requirements.txt -r docs/requirements.txt

install-req: pip
	python -m pip install --upgrade -r requirements.txt

install-req-all: pip
	python -m pip install --upgrade -r requirements.txt -r docs/requirements.txt

install-req-docs: pip
	python -m pip install --upgrade -r docs/requirements.txt

uninstall:
	pip uninstall -y urwidgets
