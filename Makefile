.PHONY: help setup lint format test clean run

help:
	@echo "NYC Landmarks Vector DB Makefile"
	@echo "================================="
	@echo "setup        - Install dependencies and set up pre-commit hooks"
	@echo "lint         - Run linters (flake8, mypy, pylint)"
	@echo "format       - Format code with black and isort"
	@echo "test         - Run tests with pytest"
	@echo "clean        - Clean cache files and build artifacts"
	@echo "run          - Run the FastAPI server"

setup:
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

lint:
	flake8 nyc_landmarks tests
	mypy --config-file=mypy.ini nyc_landmarks
	pylint nyc_landmarks

format:
	isort nyc_landmarks tests
	black nyc_landmarks tests

test:
	pytest --cov=nyc_landmarks tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .coverage -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/

run:
	python -m uvicorn nyc_landmarks.main:app --reload
