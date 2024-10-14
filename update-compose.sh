#!/bin/bash

# Install necessary packages
apk add --no-cache git bash docker-cli curl cron

# Set the GitHub repository URL and paths for compose file and script
REPO_URL=${REPO_URL:-"https://github.com/your-repo/your-project.git"}
COMPOSE_FILE_PATH=${COMPOSE_FILE_PATH:-"docker-compose.yml"}
SCRIPT_FILE_PATH=${SCRIPT_FILE_PATH:-"update-compose.sh"}
REPO_DIR="/app/repo"

# Clone or update the GitHub repository
if [ ! -d "$REPO_DIR/.git" ]; then
  echo "Cloning repository..."
  git clone $REPO_URL $REPO_DIR
else
  echo "Updating repository..."
  cd $REPO_DIR && git pull
fi

# Download the docker-compose.yml from GitHub
if [ -f "$REPO_DIR/$COMPOSE_FILE_PATH" ]; then
  echo "Applying the latest docker-compose.yml..."
  docker-compose -f $REPO_DIR/$COMPOSE_FILE_PATH pull
  docker-compose -f $REPO_DIR/$COMPOSE_FILE_PATH up -d
else
  echo "docker-compose.yml not found!"
fi

# Run the update script if it exists
if [ -f "$REPO_DIR/$SCRIPT_FILE_PATH" ]; then
  echo "Running update script..."
  bash $REPO_DIR/$SCRIPT_FILE_PATH
else
  echo "No update script found."
fi

# Set up cron job to run daily at midnight
echo "0 0 * * * /usr/local/bin/update-compose.sh >> /var/log/cron.log 2>&1" > /etc/crontabs/root
crond -f
