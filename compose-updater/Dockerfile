# Use Python slim as the base image
FROM python:3.10-slim

# Install necessary tools: git, curl, Docker, Docker Compose, and Flask
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    git \
    apt-transport-https \
    ca-certificates \
    gnupg2 \
    lsb-release && \
    # Add Docker’s official GPG key
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    # Add Docker apt repository
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    # Install Docker
    apt-get install -y docker.io && \
    # Manually install Docker Compose from GitHub releases
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
    chmod +x /usr/local/bin/docker-compose && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Flask for the API
RUN pip install flask docker gunicorn

# Set working directory
WORKDIR /app

# Copy the start.sh and Flask app to the container
COPY start.sh /app/start.sh
COPY health_check_api.py /app/health_check_api.py
RUN chmod +x /app/start.sh

# Set the entrypoint to run the script
CMD ["/bin/bash", "/app/start.sh"]
