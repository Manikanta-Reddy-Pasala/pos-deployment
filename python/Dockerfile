# Use Python slim as the base image
FROM python:3.10-slim

# Install necessary tools: git, Docker, Docker Compose, and Flask
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    git \
    apt-transport-https \
    ca-certificates \
    gnupg2 \
    software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
    apt-get update && \
    apt-get install -y docker-ce-cli docker-compose && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Flask for the API
RUN pip install flask docker

# Set working directory
WORKDIR /app

# Copy the start.sh and Flask app to the container
COPY start.sh /app/start.sh
COPY health_check_api.py /app/health_check_api.py
RUN chmod +x /app/start.sh

# Set the entrypoint to run the script
CMD ["/bin/bash", "/app/start.sh"]
