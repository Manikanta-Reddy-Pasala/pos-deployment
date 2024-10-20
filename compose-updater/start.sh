#!/bin/bash

# Function to pull the latest docker-compose.yml from GitHub and apply only if changes are detected
pull_and_apply_compose() {
  # Check if the repo already exists
  if [ ! -d "/app/repo" ]; then
    git clone $GITHUB_REPO /app/repo
  else
    cd /app/repo
    git fetch
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse @{u})

    # Only proceed if the remote has new changes
    if [ "$LOCAL" != "$REMOTE" ]; then
      echo "Changes detected, pulling updates..."
      git pull
      docker-compose -f /app/repo/$COMPOSE_FILE_PATH pull
      docker-compose -f /app/repo/$COMPOSE_FILE_PATH up -d --no-recreate
    else
      echo "No changes detected, skipping docker-compose up."
    fi
  fi
}

# Initial pull and apply
pull_and_apply_compose

# Start Gunicorn for production-ready Flask API, bind to localhost only
gunicorn -w 4 -b 127.0.0.1:5000 health_check_api:app

# Periodically check for updates every 20 seconds
while true; do
  pull_and_apply_compose
  sleep 20
done
