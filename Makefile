.PHONY: help setup lint format test clean run diff pre-commit pre-commit-update check-env sonar sonar-start sonar-stop sonar-reset-password

help:
	@echo "NYC Landmarks Vector DB Makefile"
	@echo "================================="
	@echo "setup              - Install dependencies and set up pre-commit hooks"
	@echo "lint               - Run linters (flake8, mypy, pylint)"
	@echo "format             - Format code with black and isort"
	@echo "test               - Run tests with pytest"
	@echo "clean              - Clean cache files and build artifacts"
	@echo "run                - Run the FastAPI server"
	@echo "check-env          - Check development environment and display configuration"
	@echo "pre-commit         - Pre-commit All Files"
	@echo "pre-commit-update  - Update pre-commit hooks to latest versions and install them"
	@echo "sonar              - Run SonarQube analysis"
	@echo "sonar-start        - Start SonarQube containers"
	@echo "sonar-stop         - Stop SonarQube containers"
	@echo "sonar-reset-password - Reset SonarQube admin password to 'admin'"

setup:
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

pre-commit-update:
	pre-commit autoupdate
	pre-commit install

lint:
	flake8 nyc_landmarks tests
	mypy --config-file=mypy.ini nyc_landmarks
	pylint nyc_landmarks

pre-commit:
	pre-commit run --all-files

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

check-env:
	python utils/check_dev_env.py

sonar:
	@echo "Running SonarQube analysis..."
	@./.sonarqube/run-analysis.sh || (echo "❌ Analysis failed. Make sure SonarQube is running with: make sonar-start" && exit 1)

sonar-reset-password:
	@echo "Resetting SonarQube admin password to 'admin'..."
	docker exec -it sonarqube-db-1 psql -U sonarqube -d sonarqube -c "UPDATE users SET crypted_password = '\$$2a\$$12\$$/ucdQMGweIY5jC8U7+IK7e6P91zNtUJvd4Fsx9iN4rOYQqiVxzCJG', salt=null WHERE login = 'admin';"
	docker restart sonarqube-sonarqube-1
	@echo "✅ Password reset. Wait 30 seconds for SonarQube to restart, then try logging in with admin/admin"

sonar-start:
	@echo "Starting SonarQube containers..."
	@./.sonarqube/start-sonarqube.sh

sonar-stop:
	@echo "Stopping SonarQube containers..."
	@./.sonarqube/stop-sonarqube.sh
