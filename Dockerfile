# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the Python script into the container
COPY monitor.py .

# Install Docker SDK for Python
RUN pip install docker

# Run the monitoring script
CMD ["python", "monitor.py"]
