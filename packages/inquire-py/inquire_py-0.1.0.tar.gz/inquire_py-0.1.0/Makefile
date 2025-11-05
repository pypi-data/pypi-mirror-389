.PHONY: help init test lint fmt check build release clean

help:
	@echo "Available commands:"
	@echo "  make init        - Initialize development environment"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting checks"
	@echo "  make fmt         - Format code"
	@echo "  make check       - Run linting and type checking"
	@echo "  make build       - Build distribution packages"
	@echo "  make release     - Create a new release (requires VERSION=x.y.z)"
	@echo "  make clean       - Clean build artifacts"

init:
	uv sync --all-extras

test:
	uv run pytest

test-cov:
	uv run pytest --cov=src/inquire --cov-report=term-missing

lint:
	uv run ruff check src/inquire

fmt:
	uv run ruff format src/inquire

check: lint
	uv run mypy src/inquire

build:
	uv build

release:
ifndef VERSION
	@echo "Error: VERSION is required"
	@echo "Usage: make release VERSION=0.2.0"
	@exit 1
endif
	@./scripts/release.sh $(VERSION)

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
