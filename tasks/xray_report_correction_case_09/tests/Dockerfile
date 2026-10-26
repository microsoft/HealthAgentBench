FROM python:3.12-slim
# Used only by Harbor's separate verifier environment (task.toml [verifier]).
# Holds the chexprompt LLM judge (legacy openai==0.28 SDK pin) and the gold
# report; the agent image no longer carries any of this. The verifier network is
# an allowlist for the judge API only ([verifier.environment] in task.toml).
# target_report.txt is written into tests/ by the bootstrap service at trial start
# (gitignored); Harbor builds this image at verification time, after bootstrap ran.
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir 'openai==0.28.0' 'aiolimiter>=1.1.0' 'git+https://github.com/microsoft/chexprompt.git@main'
WORKDIR /workspace
COPY harbor_evaluator.py verify_meta_task.py target_report.txt test.sh /tests/
RUN mkdir -p /logs/verifier && chmod +x /tests/test.sh
CMD ["sleep", "infinity"]
