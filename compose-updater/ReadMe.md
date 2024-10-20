<!-- @format -->

# Compose Updater & Docker Health Checker

This repository contains a Python-based application that:

- Periodically pulls the latest `docker-compose.yml` from a GitHub repository.
- Applies the `docker-compose.yml` file, pulling and updating only if changes are detected.
- Exposes a Flask-based API to check the health of running Docker containers and download logs.

The application is designed to be run in a Docker container with the ability to access the Docker socket. It uses **Gunicorn** as the WSGI server for production deployment.

## Features

1. **Automatic Docker Compose Updates**:

   - The application checks the GitHub repository for changes every 20 seconds.
   - If a new `docker-compose.yml` file is detected, it pulls the latest images and applies the Docker Compose changes without recreating unchanged containers.

2. **Health Check API**:

   - The Flask app exposes a `/health` endpoint, which returns the health status (running/stopped) of all running Docker containers.

3. **Logs Download API**:
   - The `/logs` endpoint generates a zip file of logs from all running containers, making it easy to retrieve container logs in one request.

## Prerequisites

- Docker
- Docker Compose
- GitHub repository containing a valid `docker-compose.yml` file

## How to Run

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-repo/compose-updater.git
cd compose-updater
```
