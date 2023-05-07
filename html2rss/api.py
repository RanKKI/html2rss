from fastapi import FastAPI, HTTPException, status

from html2rss.config import config
from html2rss.rss import rss

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    config.load_config()


@app.route("/rss/{alias_or_url}", status_code=status.HTTP_200_OK)
async def rss(alias_or_url: str):
    conf = config.find_config(alias_or_url)
    if not conf:
        raise HTTPException(
            status_code=404, detail=f"Config not found for {alias_or_url}"
        )
    return rss.generate(conf)
