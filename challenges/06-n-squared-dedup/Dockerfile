FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask

COPY dedup.py /app/dedup.py
COPY verify/ /app/

EXPOSE 8080

CMD ["python", "server.py"]
