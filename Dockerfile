FROM 3.10-alpine

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

COPY . /app/

ENTRYPOINT [ "uvicorn", "html2rss:app", "--log-config ./conf/log.yml" ]