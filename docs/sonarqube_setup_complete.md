# SonarQube Setup and Configuration

## Overview

This document describes the setup and configuration of SonarQube for local development in the NYC Landmarks Vector DB project. SonarQube provides code quality analysis and identifies potential issues in the codebase.

## Implementation Details

### Directory Structure

All SonarQube-related configurations and scripts are organized in the `.sonarqube/` directory:

```
.sonarqube/
├── docker-compose.yml     # Docker configuration for SonarQube and PostgreSQL
├── sonar-project.properties # Project configuration for analysis
├── setup-token.sh         # Script to set up authentication token
├── start-sonarqube.sh     # Script to start SonarQube containers
├── stop-sonarqube.sh      # Script to stop SonarQube containers
├── run-analysis.sh        # Script to run code analysis
└── token                  # Generated token file (gitignored)
```

### Authentication System

The SonarQube instance uses token-based authentication for API access:

1. Tokens are automatically generated during startup using the SonarQube API
1. Tokens are stored in the `.sonarqube/token` file (excluded from git)
1. All API interactions and analysis runs use this token for authentication
1. The web UI remains accessible without authentication for easier local development

### Scripts

#### `start-sonarqube.sh`

Starts the SonarQube and PostgreSQL containers, waits for initialization, and automatically sets up the authentication token.

```bash
.sonarqube/start-sonarqube.sh
```

#### `stop-sonarqube.sh`

Stops and removes the SonarQube and PostgreSQL containers.

```bash
.sonarqube/stop-sonarqube.sh
```

#### `run-analysis.sh`

Runs unit tests with coverage and then executes a SonarQube analysis on the project using the authentication token. The script:

1. Runs unit tests with pytest coverage targeting `tests/unit`
1. Generates both XML coverage report (`coverage.xml`) and JUnit test results (`test-results.xml`)
1. Submits the code analysis along with the test reports to SonarQube

```bash
.sonarqube/run-analysis.sh
```

#### `setup-token.sh`

Creates an authentication token for API access. This script is automatically called by `start-sonarqube.sh` but can also be run manually if needed.

```bash
.sonarqube/setup-token.sh
```

## Usage

### Starting SonarQube

```bash
.sonarqube/start-sonarqube.sh
```

Once started, the SonarQube dashboard is available at http://localhost:9000. Default credentials are admin/admin.

### Running Code Analysis

```bash
.sonarqube/run-analysis.sh
```

This will analyze the codebase and upload the results to SonarQube. After completion, view the results at http://localhost:9000/dashboard?id=nyc-landmarks-vector-db.

### Stopping SonarQube

```bash
.sonarqube/stop-sonarqube.sh
```

## Integration with Makefile

The Makefile includes targets for SonarQube management:

```bash
# Start SonarQube
make sonar-start

# Run analysis
make sonar-analyze

# Stop SonarQube
make sonar-stop
```

## Key Features

- **Token-based Authentication**: Secure API access using authentication tokens
- **Automatic Token Generation**: Tokens are automatically generated during startup
- **Docker-based Setup**: Containerized SonarQube and PostgreSQL for easy deployment
- **Simplified Local Development**: Web UI accessible without authentication
- **Project Configuration**: Pre-configured project settings for analysis
- **Python Version Specification**: Configured for Python 3.12 for more accurate analysis
- **Comprehensive Test Reporting**: JUnit XML test reports and coverage data
- **Exclusion Patterns**: Configuration to exclude test files, build artifacts, etc.

## Analysis Results

The SonarQube analysis provides:

- Code quality metrics (bugs, vulnerabilities, code smells)
- Code duplication detection
- Lines of code metrics
- Code coverage metrics from unit tests
- Detailed issue reports with resolution suggestions
- Quality gate status
