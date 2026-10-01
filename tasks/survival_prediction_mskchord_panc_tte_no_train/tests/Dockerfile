FROM python:3.12-slim

RUN pip install --no-cache-dir numpy==2.5.1 pandas==2.3.3

WORKDIR /workspace
COPY harbor_evaluator.py evaluate.py verify.py baseline.json test_labels.csv train_outcomes.csv test.sh /tests/
RUN mkdir -p /logs/verifier /logs/artifacts && chmod +x /tests/test.sh
CMD ["sleep", "infinity"]
