#!/usr/bin/make -f
SHELL := /bin/bash

.PHONY: help
help: 										## Lists all available makefile targets.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)


.PHONY: clean
clean:										## Cleans the environment.
	rm -rf venv/
	rm -rf .pytest_cache
	rm -rf dist/
	find . -path '*/__pycache__/*' -delete
	find . -type d -iname '__pycache__' -delete
	find . -type f -iname '*.pyc' -delete
	find . -type d -iname '*.egg-info' -exec rm -r {} \;


.PHONY: venv
venv:										## Initiates the venv environment and installs the required packages.
	python3 -m venv venv
	( \
		source venv/bin/activate; \
		pip3 install --upgrade pip; \
		pip3 install -r requirements.txt; \
		pip3 install -r requirements-flake10.txt; \
	)
	source venv/bin/activate


.PHONY: lint 
lint:										## Performs a lint checking.
	flake8 .
	black . --check


.PHONY: format
format:										## Autoformats the code. 
	autoflake . -r --in-place --remove-all-unused-imports --exclude venv
	black .
	isort .
