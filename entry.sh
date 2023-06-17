printenv >> /etc/environment
uvicorn html2rss.api:app --log-config ./conf/log.yml