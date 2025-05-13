.PHONY: help setup lint format test clean run diff

help:
	@echo "NYC Landmarks Vector DB Makefile"
	@echo "================================="
	@echo "setup        - Install dependencies and set up pre-commit hooks"
	@echo "lint         - Run linters (flake8, mypy, pylint)"
	@echo "format       - Format code with black and isort"
	@echo "test         - Run tests with pytest"
	@echo "clean        - Clean cache files and build artifacts"
	@echo "run          - Run the FastAPI server"
	@echo "diff         - Run the diff tool (example usage)"

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

diff:
	@echo "Diff Tool Examples:"
	@echo "-------------------"
	@echo "Compare files:"
	@echo "  python scripts/diff_tool.py file file1.py file2.py --color"
	@echo "  python scripts/diff_tool.py file file1.py file2.py --html --browser"
	@echo ""
	@echo "Compare vectors:"
	@echo "  python scripts/diff_tool.py vector vector1.npy vector2.npy --plot --output diff_plot.png"
	@echo ""
	@echo "Compare DataFrames:"
	@echo "  python scripts/diff_tool.py dataframe data1.csv data2.csv --output diff.csv"
	@echo ""
	@echo "Running diff tool test:"
	chmod +x scripts/diff_tool.py
	python -m pytest tests/unit/test_diff_utils.py -v
