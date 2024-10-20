#!/bin/bash

# Function to pull the latest docker-compose.yml from GitHub and apply only if changes are detected
pull_and_apply_compose() {
  # Check if the repo already exists
  if [ ! -d "/app/repo" ]; then
    # Clone the repository if it doesn't exist
    git clone $GITHUB_REPO /app/repo
  else
    # Pull the latest changes if the repository exists
    cd /app/repo
    git fetch
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse @{u})

    # Only proceed if the remote has new changes
    if [ "$LOCAL" != "$REMOTE" ]; then
      echo "Changes detected, pulling updates..."
      git pull
      # Pull the latest images and bring up only changed services without recreating existing ones
      docker-compose -f /app/repo/$COMPOSE_FILE_PATH pull
      docker-compose -f /app/repo/$COMPOSE_FILE_PATH up -d --no-recreate
    else
      echo "No changes detected, skipping docker-compose up."
    fi
  fi
}

# Initial pull and apply
pull_and_apply_compose

# Start the Flask app for container health API
python3 /app/health_check_api.py &

# Periodically check for updates every 20 seconds
while true; do
  pull_and_apply_compose
  sleep 20
done
