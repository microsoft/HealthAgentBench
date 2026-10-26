FROM python:3.12-slim
# This image is used only by Harbor's separate verifier environment.
WORKDIR /workspace
COPY evaluator.py answer_key.json test.sh /tests/
RUN mkdir -p /logs/verifier && chmod +x /tests/test.sh
CMD ["sleep", "infinity"]
