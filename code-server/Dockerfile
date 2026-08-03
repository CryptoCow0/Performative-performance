# In-browser workspace (VS Code) that teams reach at
# https://<team>.performative-performance.com
# Ships with psql + curl so teams can drive the challenge containers from the
# integrated terminal by Docker service name (e.g. `psql -h challenge-01-db`).
FROM codercom/code-server:latest

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client curl \
    && rm -rf /var/lib/apt/lists/*
USER coder
