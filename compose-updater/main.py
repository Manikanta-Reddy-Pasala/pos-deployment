from flask import Flask, jsonify, send_file
import docker
import os
import zipfile
import time
import subprocess
import threading
import git
import shutil
import logging

app = Flask(__name__)

# Initialize Docker client
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

# Logging setup
logging.basicConfig(level=logging.INFO)

# Environment variables
REQUIRED_SERVICES = os.getenv('REQUIRED_SERVICES', 'compose-updater,mongodb,nats-server,posNodeBackend,posbackend,watchtower').split(',')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'https://github.com/Manikanta-Reddy-Pasala/pos-deployment.git')
COMPOSE_FILE_PATH = os.getenv('COMPOSE_FILE_PATH', 'docker-compose/docker-compose.yaml')
REPO_DIR = '/app/repo'
LOG_DIR = "/app/logs"
EXCLUDED_LOGS = ["mongodb.log", "watchtower.log", "nats-server.log", "compose-updater.log"]

def pull_and_apply_compose():
    logging.info("Checking for updates in the repository...")
    try:
        if os.path.exists(REPO_DIR):
            if os.path.isdir(REPO_DIR):
                try:
                    repo = git.Repo(REPO_DIR)
                    logging.info(f"Using existing repository in {REPO_DIR}")
                except git.exc.InvalidGitRepositoryError:
                    logging.warning(f"Invalid Git repository. Cleaning up {REPO_DIR}...")
                    shutil.rmtree(REPO_DIR)
                    logging.info(f"Deleted {REPO_DIR}. Cloning fresh repository.")
                    repo = git.Repo.clone_from(GITHUB_REPO, REPO_DIR)
            else:
                logging.error(f"{REPO_DIR} exists but is not a directory. Aborting.")
                return
        else:
            logging.info(f"Cloning repository from {GITHUB_REPO} into {REPO_DIR}...")
            repo = git.Repo.clone_from(GITHUB_REPO, REPO_DIR)

        # Ensure we are on the master branch
        if repo.active_branch.name != 'master':
            logging.info("Switching to master branch...")
            repo.git.checkout('master')

        # Force reset to remove local changes (if any) and ensure the repo is clean
        logging.info("Resetting repository to the latest commit from origin...")
        repo.git.reset('--hard', 'origin/master')

        # Fetch the latest changes from the origin
        repo.remotes.origin.fetch()
        latest = repo.remotes.origin.refs.master.commit  # Get the latest commit from remote master
        current = repo.head.commit  # Get the current commit in the local repo

        logging.info(f"Current commit: {current}, Latest commit: {latest}")

        # Pull the latest changes if there are any
        if current != latest:
            logging.info("Changes detected, pulling updates...")
            repo.remotes.origin.pull('master')
            subprocess.run(['docker-compose', '-f', f"{REPO_DIR}/{COMPOSE_FILE_PATH}", 'pull'], check=True)
            subprocess.run(['docker-compose', '-f', f"{REPO_DIR}/{COMPOSE_FILE_PATH}", 'up', '-d', '--no-recreate'], check=True)
        else:
            logging.info("No changes detected, skipping docker-compose up.")

    except Exception as e:
        logging.error(f"Error during the pull-and-apply process: {e}")

# Function to run periodic checks
def periodic_check():
    while True:
        logging.info("Starting periodic update check...")
        pull_and_apply_compose()
        logging.info("Waiting for the next update cycle...")
        time.sleep(20)

# Run the periodic check in a separate thread
def start_periodic_check():
    logging.info("Starting periodic check thread...")
    periodic_thread = threading.Thread(target=periodic_check)
    periodic_thread.daemon = True
    periodic_thread.start()

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    containers = client.containers.list()
    status = {}
    all_services_running = True

    for required_service in REQUIRED_SERVICES:
        container_status = next((container.status for container in containers if container.name == required_service), 'not found')
        if container_status != 'running':
            all_services_running = False
        status[required_service] = container_status

    if all_services_running:
        return jsonify({"status": "success", "message": "All services are running"}), 200
    else:
        return jsonify({"status": "failure", "message": "One or more services are not running", "details": status}), 500

# Logs download endpoint
@app.route('/logs', methods=['GET'])
def download_logs():
    zip_filename = f"/app/logs_{int(time.time())}.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, _, files in os.walk(LOG_DIR):
            for file in files:
                if file not in EXCLUDED_LOGS:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, arcname=file)
    return send_file(zip_filename, as_attachment=True)

# Get CPU and memory usage of a container
def get_cpu_memory_usage(container):
    stats = container.stats(stream=False)
    
    # Calculate CPU usage
    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
    system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
    num_cpus = len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [1]))
    cpu_percentage = (cpu_delta / system_delta) * num_cpus * 100 if system_delta > 0 else 0
    
    # Calculate memory usage
    memory_usage = stats['memory_stats']['usage']
    memory_limit = stats['memory_stats']['limit']
    memory_percentage = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
    
    return {
        'cpu_usage': f"{cpu_percentage:.2f}%",
        'memory_usage': f"{memory_usage / (1024 ** 2):.2f} MB",
        'memory_percentage': f"{memory_percentage:.2f}%"
    }

# CPU and memory usage endpoint
@app.route('/cpu-memory-usage', methods=['GET'])
def cpu_memory_usage():
    usage_stats = {}
    containers = client.containers.list()

    for container in containers:
        try:
            usage = get_cpu_memory_usage(container)
            usage_stats[container.name] = usage
        except Exception as e:
            usage_stats[container.name] = f"Error retrieving usage: {str(e)}"
    
    return jsonify(usage_stats)

if __name__ == '__main__':
    start_periodic_check()
    app.run(host='0.0.0.0', port=5000)
