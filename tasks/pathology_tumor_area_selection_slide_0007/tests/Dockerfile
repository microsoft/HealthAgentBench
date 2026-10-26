FROM python:3.12-slim
# Used only by Harbor's separate verifier environment (task.toml [verifier]).
# The answer key carries precomputed expected_tumor_tiles, so scoring needs no
# slide, mask or network; the slide-based coverage diagnostic is skipped here.
WORKDIR /workspace
COPY harbor_evaluator.py evaluator.py verify_meta_task.py task_answer_key.json test.sh /tests/
RUN mkdir -p /logs/verifier && chmod +x /tests/test.sh
CMD ["sleep", "infinity"]
