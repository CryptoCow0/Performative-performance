FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask requests aiohttp

COPY process_images.py /app/process_images.py
COPY verify/ /app/

EXPOSE 8080

CMD ["python", "server.py"]
