from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
import httpx
import os
import datetime
import psutil
import sys
from pydantic import BaseModel
import zlib
import brotli
from redis import Redis

# logging
import logging
from loguru import logger

from utils import (
    StubbedGunicornLogger,
    InterceptHandler,
    StandaloneApplication,
    hashfunc,
    colors
)


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

json_logs = False  # set it to True if you don't love yourselves
log_level = logging.getLevelName("INFO")


redis = Redis()
PASTE_URL = None

@app.on_event("startup")
def startup():
    load_dotenv()
    global redis, PASTE_URL
    redis = Redis(host="localhost", port=6379, decode_responses=False, encoding="utf-8")
    PASTE_URL = os.getenv("PASTE_URL")


class ResponseItem(BaseModel):
    hash: str
    url: str

# class RequestItem(BaseModel):
#     raw_text: 


@app.get("/", response_model=None, response_class=Response)
async def getter() -> Response:  # type: ignore
    return HTMLResponse(content="Hello world!", status_code=200)

@app.get("/{hash_key}", response_model=None, response_class=Response)
async def getter(hash_key: str, raw: str | None = None) -> HTMLResponse | Response:  # type: ignore
    value = "" # important
    try:
        value = brotli.decompress(redis.get(hash_key))          #.encode().decode('unicode_escape').encode("raw_unicode_escape")[3:-1])
    except TypeError as e:
        if str(e) != "object of type 'NoneType' has no len()":
            raise
        else:
            pass
    if raw not in ("True", "true", "1"):
        value = colors(value)
        return HTMLResponse(content=value + "<link rel=\"stylesheet\" href=\"static/styles.css\">", status_code=200)
    return Response(content=value, status_code=200)


# @app.post("/", response_model=None, response_class=Response)
# async def poster(request: Request) -> Response: # type: ignore
#     text = await request.body() # plan to save raw text as is in the database
#     return Response(content=zlib.compress(text, level=9), status_code=200)

# @app.post("/uncompress", response_model=None, response_class=Response)
# async def poster(request: Request) -> Response: # type: ignore
#     text = await request.body() # plan to save raw text as is in the database
#     return Response(content=text.decode(), status_code=200)


@app.post("/", response_model=None, response_class=Response)
async def poster(request: Request): # type: ignore
    text = await request.body() # plan to save raw text as is in the database
    hash = hashfunc()
    redis.set(hash, brotli.compress(text, quality=11))
    return Response(content=f"{PASTE_URL}/{hash}", status_code=200)


if __name__ == "__main__":
    intercept_handler = InterceptHandler()
    logging.root.setLevel(log_level)
    seen = set()
    for name in [
        *logging.root.manager.loggerDict.keys(),
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            logging.getLogger(name).handlers = [intercept_handler]

    logger.configure(handlers=[{"sink": sys.stdout, "serialize": json_logs}])

    options = {
        "bind": "0.0.0.0:8010",
        "workers": len(psutil.Process().cpu_affinity()),  # type: ignore
        "accesslog": "-",
        "errorlog": "-",
        "worker_class": "uvicorn.workers.UvicornWorker",
        "logger_class": StubbedGunicornLogger,
        "reload": "True",
        "reload_engine": "inotify",  # requires inotify package
    }

    StandaloneApplication("__main__:app", options).run()
