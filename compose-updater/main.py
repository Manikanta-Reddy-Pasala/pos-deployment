from flask import Flask, jsonify, send_file
import docker
import os
import zipfile
import time
import subprocess
import threading
import git
import shutil

app = Flask(__name__)

# Initialize Docker client
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

# Environment variables
REQUIRED_SERVICES = os.getenv('REQUIRED_SERVICES', 'compose-updater,mongodb,nats-server,posNodeBackend,posbackend,watchtower').split(',')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'https://github.com/Manikanta-Reddy-Pasala/pos-deployment.git')
COMPOSE_FILE_PATH = os.getenv('COMPOSE_FILE_PATH', 'docker-compose/docker-compose.yaml')
REPO_DIR = '/app/repo'
LOG_DIR = "/app/logs"
EXCLUDED_LOGS = ["mongodb.log", "watchtower.log", "nats-server.log", "compose-updater.log"]


# Function to pull the latest docker-compose.yml from GitHub and apply only if changes are detected
def pull_and_apply_compose():
    try:
        if os.path.exists(REPO_DIR):
            if os.path.isdir(REPO_DIR):
                try:
                    repo = git.Repo(REPO_DIR)
                    print(f"Using existing repository in {REPO_DIR}")
                except git.exc.InvalidGitRepositoryError:
                    print(f"Invalid Git repository. Cleaning up {REPO_DIR}...")
                    shutil.rmtree(REPO_DIR)
                    print(f"Deleted {REPO_DIR}. Cloning fresh repository.")
                    repo = git.Repo.clone_from(GITHUB_REPO, REPO_DIR)
            else:
                print(f"{REPO_DIR} exists but is not a directory. Aborting.")
                return
        else:
            print(f"Cloning repository from {GITHUB_REPO} into {REPO_DIR}...")
            repo = git.Repo.clone_from(GITHUB_REPO, REPO_DIR)
        
        if repo.active_branch.name != 'master':
            print("Switching to master branch...")
            repo.git.checkout('master')
        
        current = repo.head.commit
        repo.remotes.origin.fetch()
        latest = repo.head.commit
        print(f"Current commit: {current}, Latest commit: {latest}")

        if current != latest:
            print("Changes detected, pulling updates...")
            repo.remotes.origin.pull('master')
            subprocess.run(['docker-compose', '-f', f"{REPO_DIR}/{COMPOSE_FILE_PATH}", 'pull'], check=True)
            subprocess.run(['docker-compose', '-f', f"{REPO_DIR}/{COMPOSE_FILE_PATH}", 'up', '-d', '--no-recreate'], check=True)
        else:
            print("No changes detected, skipping docker-compose up.")
    
    except Exception as e:
        print(f"Error during the pull-and-apply process: {e}")

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

    # Check if all required services are running
    all_services_running = True
    for required_service in REQUIRED_SERVICES:
        container_status = next((container.status for container in containers if container.name == required_service), 'not found')
        if container_status != 'running':
            all_services_running = False
        status[required_service] = container_status

    # Return success or failure based on the status of the services
    if all_services_running:
        return jsonify({"status": "success", "message": "All services are running"}), 200
    else:
        return jsonify({"status": "failure", "message": "One or more services are not running", "details": status}), 500

# Route to download logs of all running containers as a zip file
@app.route('/logs', methods=['GET'])
def download_logs():
    # Create a unique zip file name
    zip_filename = f"/app/logs_{int(time.time())}.zip"
    
    # Create a zip file and add only relevant log files
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, dirs, files in os.walk(LOG_DIR):
            for file in files:
                if file not in EXCLUDED_LOGS:  # Exclude unwanted logs
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, arcname=file)  # Add the file to the zip archive
    
    # Return the zip file as a downloadable attachment
    return send_file(zip_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
