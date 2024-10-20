from flask import Flask, jsonify, send_file
import docker
import os
import zipfile
import time

app = Flask(__name__)

# Initialize Docker client
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

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
    app.run(host='0.0.0.0', port=5000)
