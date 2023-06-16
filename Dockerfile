FROM python:3.10-slim-buster

WORKDIR /app

RUN apt-get update && apt-get install -y cron
COPY ./rssbot/cron /etc/cron.d/botcron
RUN chmod 0644 /etc/cron.d/botcron && crontab /etc/cron.d/botcron

COPY requirements.txt .

RUN pip install -r /app/requirements.txt

COPY . /app/

ENV UVICORN_HOST="0.0.0.0" UVICORN_PORT="8000"

ENTRYPOINT [ "uvicorn", "html2rss.api:app", "--log-config", "./conf/log.yml" ]