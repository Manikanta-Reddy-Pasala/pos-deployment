from flask import Flask, jsonify, send_file
import docker
import os
import zipfile
import time
import subprocess
import threading
import git

app = Flask(__name__)

# Initialize Docker client
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

# Environment variables
GITHUB_REPO = os.getenv('GITHUB_REPO', 'https://github.com/Manikanta-Reddy-Pasala/pos-deployment.git')
COMPOSE_FILE_PATH = os.getenv('COMPOSE_FILE_PATH', 'docker-compose/docker-compose.yaml')
REPO_DIR = '/app/repo'

# Function to pull the latest docker-compose.yml from GitHub and apply only if changes are detected
def pull_and_apply_compose():
    if not os.path.exists(REPO_DIR):
        # Clone the repository if it doesn't exist
        git.Repo.clone_from(GITHUB_REPO, REPO_DIR)
    else:
        # Check if there are any changes
        repo = git.Repo(REPO_DIR)
        current = repo.head.commit
        repo.remotes.origin.fetch()
        latest = repo.head.commit

        if current != latest:
            print("Changes detected, pulling updates...")
            repo.remotes.origin.pull()
            # Pull the latest images and bring up only changed services without recreating existing ones
            subprocess.run(['docker-compose', '-f', f"{REPO_DIR}/{COMPOSE_FILE_PATH}", 'pull'], check=True)
            subprocess.run(['docker-compose', '-f', f"{REPO_DIR}/{COMPOSE_FILE_PATH}", 'up', '-d', '--no-recreate'], check=True)
        else:
            print("No changes detected, skipping docker-compose up.")

# Periodically check for updates every 20 seconds
def periodic_check():
    while True:
        pull_and_apply_compose()
        time.sleep(20)

# Start the periodic update check in a background thread
thread = threading.Thread(target=periodic_check)
thread.daemon = True
thread.start()

# Route to check the health of all running containers
@app.route('/health', methods=['GET'])
def health_check():
    containers = client.containers.list()
    status = {}
    for container in containers:
        container_info = {
            'status': container.status,
            'name': container.name
        }
        status[container.name] = container_info
    return jsonify(status)

# Route to download logs of all running containers as a zip file
@app.route('/logs', methods=['GET'])
def download_logs():
    log_dir = "/app/logs"
    zip_filename = f"/app/logs_{int(time.time())}.zip"
    
    # Create a zip file of logs
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for container in client.containers.list():
            log_file_path = os.path.join(log_dir, f"{container.name}.log")
            with open(log_file_path, 'w') as f:
                f.write(container.logs().decode('utf-8'))
            zipf.write(log_file_path, arcname=f"{container.name}.log")
    
    return send_file(zip_filename, as_attachment=True)

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='127.0.0.1', port=5000)
