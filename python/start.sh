#!/bin/bash

# Function to pull the latest docker-compose.yml from GitHub and apply it
pull_and_apply_compose() {
  if [ ! -d "/app/repo" ]; then
    git clone $GITHUB_REPO /app/repo
  else
    cd /app/repo && git pull
  fi

  docker-compose -f /app/repo/$COMPOSE_FILE_PATH up -d
}

# Initial pull and apply
pull_and_apply_compose

# Start Flask app for container health and log API
python3 /app/health_check_api.py &

# Periodically pull and apply the latest docker-compose.yml every 20 seconds
while true; do
  pull_and_apply_compose
  sleep 20
done
