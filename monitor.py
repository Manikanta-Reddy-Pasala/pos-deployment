import os
import time
import docker

# Set thresholds
CPU_THRESHOLD = 80  # 80% CPU usage
MEMORY_THRESHOLD = 80  # 80% Memory usage

# Initialize Docker client
client = docker.from_env()

def get_container_stats(container):
    stats = container.stats(stream=False)
    
    # CPU usage calculation
    try:
        cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage']
        system_cpu_usage = stats['cpu_stats']['system_cpu_usage']
        cpu_percent = (cpu_usage / system_cpu_usage) * 100
    except KeyError:
        cpu_percent = 0  # If there is any issue, set to 0 or log as needed
    
    # Memory usage calculation
    memory_usage = stats['memory_stats']['usage']
    memory_limit = stats['memory_stats']['limit']
    memory_percent = (memory_usage / memory_limit) * 100

    return cpu_percent, memory_percent

def check_and_restart(container_name):
    try:
        container = client.containers.get(container_name)
        cpu_percent, memory_percent = get_container_stats(container)

        # Print CPU and memory usage on every scan (flush to ensure immediate output)
        print(f"Container: {container_name} - CPU: {cpu_percent:.2f}% - Memory: {memory_percent:.2f}%", flush=True)

        if cpu_percent > CPU_THRESHOLD:
            print(f"CPU usage is above threshold for {container_name}. Restarting...", flush=True)
            container.restart()

        if memory_percent > MEMORY_THRESHOLD:
            print(f"Memory usage is above threshold for {container_name}. Restarting...", flush=True)
            container.restart()

    except docker.errors.NotFound:
        print(f"Container {container_name} not found.", flush=True)

def monitor_containers():
    while True:
        # List of containers to monitor
        containers_to_monitor = ["posbackend", "mongodb", "nats-server"]
        
        for container_name in containers_to_monitor:
            check_and_restart(container_name)
        
        time.sleep(60)  # Wait for 60 seconds before checking again

if __name__ == "__main__":
    monitor_containers()
