FROM python:3.12-slim
# Used only by Harbor's separate verifier environment (task.toml [verifier]).
# Same numpy/pandas/scikit-learn pins as the agent image: evaluate.py scores
# AUROC/AUPRC/Brier with sklearn.metrics and the pins keep scoring identical.
# test_labels.csv is written into tests/ by the bootstrap service at trial start
# (gitignored); Harbor builds this image at verification time, after bootstrap ran.
RUN pip install --no-cache-dir numpy==2.1.3 pandas==2.2.3 scikit-learn==1.5.2
WORKDIR /workspace
COPY harbor_evaluator.py evaluate.py verify.py test_labels.csv baseline.json test.sh /tests/
RUN mkdir -p /logs/verifier && chmod +x /tests/test.sh
CMD ["sleep", "infinity"]
