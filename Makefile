.PHONY: clean install formatter lint test types docs livedocs

JOBS ?= 1

help:
	@echo "make"
	@echo "    clean"
	@echo "        Remove Python/build artifacts."
	@echo "    install"
	@echo "        Install capella_console_client."
	@echo "    formatter"
	@echo "        Apply black formatting to code."
	@echo "    lint"
	@echo "        Check the code style."
	@echo "    test"
	@echo "        Run the unit tests."
	@echo "    types"
	@echo "        Check for type errors using pytype."
	@echo "    docs"
	@echo "        Build the documentation."
	@echo "    livedocs"
	@echo "        Build the documentation with a live preview for quick iteration."

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f  {} +
	rm -rf build/
	rm -rf capella_console_client.egg-info/
	rm -rf .mypy_cache/
	rm -rf .pytest_cache/
	rm -rf dist/

install:
	poetry install

formatter:
	poetry run black .

lint:
	poetry run black --check --diff .

test:
	poetry run pytest --cov capella_console_client --cov-report=html -sv

types:
	poetry run mypy --install-types --non-interactive capella_console_client --tb
docs:
	poetry run make -C docs html O=-v

livedocs:
	poetry run sphinx-autobuild docs docs/build/html
