.PHONY: clean install formatter lint test types docs livedocs security

JOBS ?= 1

help:
	@echo "make"
	@echo "    clean"
	@echo "        Remove Python/build artifacts."
	@echo "    install"
	@echo "        Install capella_console_client."
	@echo "    formatter"
	@echo "        Apply ruff formatting and auto-fix lint issues."
	@echo "    lint"
	@echo "        Check code style and lint (ruff format + check)."
	@echo "    test"
	@echo "        Run the unit tests."
	@echo "    types"
	@echo "        Check for type errors using pytype."
	@echo "    docs"
	@echo "        Build the documentation."
	@echo "    livedocs"
	@echo "        Build the documentation with a live preview for quick iteration."
	@echo "    security"
	@echo "        Run security scans (bandit + pip-audit)."

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
	uv sync --all-extras

formatter:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff format --check .
	uv run ruff check .

test:
	uv run pytest --cov capella_console_client --cov-report=html -sv

types:
	uv run mypy --install-types --non-interactive capella_console_client --tb
docs:
	uv run make -C docs html O=-v

livedocs:
	uv run sphinx-autobuild docs docs/build/html

security:
	uv run bandit -r capella_console_client -f json --exit-zero 2>/dev/null | python3 scripts/bandit_report.py
	uv run pip-audit
