FROM python:3.12-slim
# Used only by Harbor's separate verifier environment (task.toml [verifier]).
# It holds the answer key; the agent's main container never receives /tests.
# gold.json is written into tests/ by the bootstrap service at trial start (it is
# gitignored); Harbor builds this image at verification time, after bootstrap ran.
WORKDIR /workspace
COPY harbor_evaluator.py verify.py gold.json test.sh /tests/
RUN mkdir -p /logs/verifier && chmod +x /tests/test.sh
CMD ["sleep", "infinity"]
