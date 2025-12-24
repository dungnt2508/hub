.PHONY: help install test lint format type-check clean run

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make type-check   - Run type checker"
	@echo "  make clean        - Clean cache files"
	@echo "  make run           - Run example"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=backend --cov-report=term-missing

lint:
	flake8 backend tests
	black --check backend tests
	isort --check backend tests

format:
	black backend tests
	isort backend tests

type-check:
	mypy backend

clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache

run:
	python examples/basic_usage.py

