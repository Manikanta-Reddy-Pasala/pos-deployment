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
GITHUB_REPO = os.getenv('GITHUB_REPO', 'https://github.com/Manikanta-Reddy-Pasala/pos-deployment.git')
COMPOSE_FILE_PATH = os.getenv('COMPOSE_FILE_PATH', 'docker-compose/docker-compose.yaml')
REPO_DIR = '/app/repo'

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
    
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for container in client.containers.list():
            log_file_path = os.path.join(log_dir, f"{container.name}.log")
            with open(log_file_path, 'w') as f:
                f.write(container.logs().decode('utf-8'))
            zipf.write(log_file_path, arcname=f"{container.name}.log")
    
    return send_file(zip_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
