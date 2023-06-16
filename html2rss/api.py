from fastapi import FastAPI, HTTPException, Response, status

from html2rss.config import config
from html2rss.rss import rss

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    config.load_config()


@app.get("/rss/{alias_or_url}", status_code=status.HTTP_200_OK)
async def rss_handler(alias_or_url: str):
    conf = config.find_config(alias_or_url)
    if not conf:
        raise HTTPException(
            status_code=404, detail=f"Config not found for {alias_or_url}"
        )
    try:
        body = await rss.generate(conf)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating RSS feed for {alias_or_url}: {e}",
        )
    return Response(content=body, media_type="application/xml")
