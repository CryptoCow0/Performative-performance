FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask requests

# Pristine copy of the editable file. On startup it is seeded into the shared
# /app/workspace volume (only if missing), so the team's browser edits reach
# this verifier while a fresh volume gets the broken baseline.
COPY fetch_profiles.py /opt/original/fetch_profiles.py
COPY verify/ /app/

EXPOSE 8080

CMD ["sh", "-c", "mkdir -p /app/workspace && for f in /opt/original/*; do n=$(basename \"$f\"); [ -e \"/app/workspace/$n\" ] || cp \"$f\" \"/app/workspace/$n\"; done && chmod -R 777 /app/workspace && exec python server.py"]
