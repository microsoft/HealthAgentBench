FROM python:3.12-slim@sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203
# This image runs separately and receives only the submitted artifact.
RUN pip install --no-cache-dir pandas==2.2.2 numpy==1.26.4 pytest==8.4.1 \
    python-dateutil==2.9.0.post0 pytz==2026.5 six==1.17.0 tzdata==2026.5 \
    iniconfig==2.3.0 packaging==26.3 pluggy==1.6.0 pygments==2.21.0
WORKDIR /workspace
COPY scoring.py test_flagged_rows.py labels.csv test.sh /tests/
RUN mkdir -p /workspace/submission /logs/verifier && chmod +x /tests/test.sh
CMD ["sleep", "infinity"]
