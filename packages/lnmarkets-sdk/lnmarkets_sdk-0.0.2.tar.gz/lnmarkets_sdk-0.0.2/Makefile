.PHONY: help install install-browsers create-api-key example lint format typecheck test check

help:
	@echo "Available commands:"
	@echo "  make install           - Install dependencies"
	@echo "  make install-browsers  - Install Playwright browsers"
	@echo "  make create-api-key    - Create API key for v3"
	@echo "  make example           - Run basic example"
	@echo "  make lint              - Run linter (ruff check)"
	@echo "  make format            - Format code (ruff format)"
	@echo "  make typecheck         - Run type checker (pyright)"
	@echo "  make check             - Run all checks (lint, typecheck)"

install:
	uv sync --all-groups

install-browsers:
	uv run playwright install chromium

create-api-key: install-browsers
	uv run python scripts/create-api-key-v3.py

example:
	uv run python examples/basic.py

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run pyright

check: lint typecheck
