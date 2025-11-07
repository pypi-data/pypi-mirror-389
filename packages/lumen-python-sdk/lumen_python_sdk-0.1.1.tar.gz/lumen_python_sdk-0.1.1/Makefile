.PHONY: help install dev test lint format clean build publish publish-test

help:
	@echo "Lumen Python SDK - Makefile Commands"
	@echo ""
	@echo "  make install       Install package dependencies with uv"
	@echo "  make dev           Install package in development mode with dev dependencies"
	@echo "  make test          Run tests with pytest"
	@echo "  make lint          Run linters (ruff, mypy)"
	@echo "  make format        Format code with black"
	@echo "  make clean         Clean build artifacts"
	@echo "  make build         Build package for distribution with uv"
	@echo "  make publish       Publish package to PyPI with uv"
	@echo "  make publish-test  Publish to TestPyPI with uv"

install:
	uv pip install -e .

dev:
	uv pip install -e ".[dev,flask,fastapi,django]"

test:
	uv run pytest

test-cov:
	uv run pytest --cov=lumen --cov-report=html --cov-report=term

lint:
	uv run ruff check lumen tests examples
	uv run mypy lumen

format:
	uv run black lumen tests examples
	uv run ruff check --fix lumen tests examples

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	uv build

publish: build
	@echo "Publishing to PyPI..."
	@echo "Make sure UV_PUBLISH_TOKEN is set or have your credentials ready"
	uv publish

publish-test: build
	@echo "Publishing to TestPyPI..."
	uv publish --publish-url https://test.pypi.org/legacy/
