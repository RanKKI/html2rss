FROM python:3.10-slim-buster

WORKDIR /app

RUN apt-get update && apt-get install -y cron

COPY requirements.txt .

RUN pip install -r /app/requirements.txt

COPY . /app/

RUN cp /app/rssbot/cron /etc/cron.d/botcron && chmod 0644 /etc/cron.d/botcron && crontab /etc/cron.d/botcron && service cron restart

ENV UVICORN_HOST="0.0.0.0" UVICORN_PORT="8000"

ENTRYPOINT [ "sh", "/app/entry.sh" ]