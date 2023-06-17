service cron restart
(crontab -l 2>/dev/null; echo "HOME=/") | crontab -
(crontab -l 2>/dev/null; echo "${HTML2RSS_CRON_INTERVAL} /usr/local/bin/python3 /app/rssbot/bot.py") | crontab -
printenv | grep "HTML2RSS_" > /etc/environment
uvicorn html2rss.api:app --log-config ./conf/log.yml