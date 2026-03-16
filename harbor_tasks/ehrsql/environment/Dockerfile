FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    jq \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy workspace files (build context is harbor_tasks/ehrsql/)
COPY environment/workspace/ /workspace/

# Copy tests directory (verifier and evaluator)
COPY tests/ /tests/

# Ensure scripts are executable
RUN chmod +x /workspace/scripts/primitives/*.py || true
RUN chmod +x /tests/test.sh || true

# Make logs directory
RUN mkdir -p /logs/verifier

# Default command (agent will be started by Harbor)
CMD ["/bin/bash"]
