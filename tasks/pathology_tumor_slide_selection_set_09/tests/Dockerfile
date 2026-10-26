FROM python:3.12-slim
# Used only by Harbor's separate verifier environment (task.toml [verifier]).
# It holds the answer key; the agent's main container never receives /tests.
WORKDIR /workspace
COPY verify.py task_answer_key.json test.sh /tests/
RUN mkdir -p /logs/verifier && chmod +x /tests/test.sh
CMD ["sleep", "infinity"]
