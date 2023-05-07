FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install -r /app/requirements.txt

COPY . /app/

ENV UVICORN_HOST="0.0.0.0" UVICORN_PORT="8000"

ENTRYPOINT [ "uvicorn", "html2rss.api:app", "--log-config", "./conf/log.yml" ]