# SonarQube Community Stack Setup

This document explains how to spin up a local SonarQube instance using Docker Compose and how to verify that it is running correctly.

## Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop) and Docker Compose installed

## Creating the Stack

1. From the project root, run the following command to start SonarQube and its PostgreSQL database:

   ```bash
   docker compose -f docker-compose.sonarqube.yml up -d
   ```

   The first start may take a few minutes while Docker pulls the images.

2. Once the services are running, open your browser to [http://localhost:9000](http://localhost:9000).
   Log in with the default credentials `admin` / `admin` and change the password when prompted.

## Testing the Setup

- Check the container status:

  ```bash
  docker compose -f docker-compose.sonarqube.yml ps
  ```

- Verify the health endpoint returns `GREEN`:

  ```bash
  curl http://localhost:9000/api/system/health
  ```

  A successful response should contain `"status":"GREEN"`.

- When finished, stop the stack:

  ```bash
  docker compose -f docker-compose.sonarqube.yml down
  ```

## Reference

For more details about the Community Edition features, see the [SonarQube Community Edition page](https://www.sonarsource.com/open-source-editions/sonarqube-community-edition/).

