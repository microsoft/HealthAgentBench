FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    jq \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies required for evaluation
RUN pip install --no-cache-dir \
    func-timeout>=4.3.5 \
    numpy>=2.4.2 \
    gdown

# Set working directory
WORKDIR /workspace

# Copy workspace files (build context is harbor_tasks/ehrsql/)
COPY environment/workspace/ /workspace/

# Copy entrypoint script
COPY environment/entrypoint.sh /entrypoint.sh

# DO NOT copy /tests directory (answer keys will be mounted at runtime by Harbor)
# This prevents agent from accessing the answer key file during task execution
# Harbor will mount tests/ directory for the verifier only

# Make logs directory
RUN mkdir -p /logs/verifier

ENTRYPOINT ["/entrypoint.sh"]

# Default command (agent will be started by Harbor)
CMD ["/bin/bash"]
