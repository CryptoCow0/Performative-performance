FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask requests

COPY fetch_profiles.py /app/fetch_profiles.py
COPY verify/ /app/

EXPOSE 8080

CMD ["python", "server.py"]
