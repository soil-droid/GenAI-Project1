# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent application code
COPY ./adk_agent /app/adk_agent

# Set workdir to where the ADK app is
WORKDIR /app/adk_agent

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Run the built-in ADK web UI
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8080"]