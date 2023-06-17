FROM python:3.10-slim-buster

WORKDIR /app

RUN apt-get update && apt-get install -y cron

COPY requirements.txt .

RUN pip install -r /app/requirements.txt

COPY . /app/

ENV UVICORN_HOST="0.0.0.0" UVICORN_PORT="8000" HTML2RSS_CRON_INTERVAL="*/30 * * * *"

ENTRYPOINT [ "sh", "/app/entry.sh" ]