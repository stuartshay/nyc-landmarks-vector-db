# SonarQube for NYC Landmarks Vector DB

This directory contains configuration and helper scripts for running SonarQube code quality analysis on the NYC Landmarks Vector DB project.

## Setup

The configuration consists of:

- `docker-compose.yml`: Docker Compose configuration for SonarQube and PostgreSQL
- `sonar-project.properties`: Project configuration for SonarQube analysis
- Helper scripts for starting, stopping, and running analysis

## Helper Scripts

- `start-sonarqube.sh`: Start the SonarQube and PostgreSQL containers
- `stop-sonarqube.sh`: Stop and remove the containers
- `run-analysis.sh`: Run SonarQube analysis on the project

## Usage

### Starting SonarQube

```bash
./.sonarqube/start-sonarqube.sh
```

This will:

- Start the SonarQube and PostgreSQL containers
- Wait for SonarQube to be fully initialized
- Provide status information

### Running Analysis

```bash
./.sonarqube/run-analysis.sh
```

This will:

- Check if SonarQube is running
- Run the analysis using sonar-scanner
- Display a link to view the results

### Stopping SonarQube

```bash
./.sonarqube/stop-sonarqube.sh
```

This will stop and remove the containers.

## Configuration Details

### Authentication

- Default credentials: `admin`/`admin`
- Authentication is disabled for local development (SONAR_FORCEAUTHENTICATION=false)
- No token is required for running analysis

### Project Configuration

- Project key: `nyc-landmarks-vector-db`
- Source directories: `nyc_landmarks` (main code), `tests` (test code)
- Various exclusions for generated files and dependencies

## Web Interface

When running, the SonarQube web interface is available at http://localhost:9000
