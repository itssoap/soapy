from hashing import hashfunc
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response

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
)


app = FastAPI()

json_logs = False  # set it to True if you don't love yourselves
log_level = logging.getLevelName("INFO")


redis = Redis()

@app.on_event("startup")
def startup():
    load_dotenv()
    global redis
    redis = Redis(host="localhost", port=6379, decode_responses=True, encoding="utf-8")


class ResponseItem(BaseModel):
    hash: str
    url: str

# class RequestItem(BaseModel):
#     raw_text: 


@app.get("/", response_model=None, response_class=Response)
async def getter() -> Response:  # type: ignore
    return HTMLResponse(content="Hello world!", status_code=200)

@app.get("/data/{hash_key}", response_model=None, response_class=Response)
async def getter(hash_key: str) -> Response:  # type: ignore
    value = brotli.decompress(redis.get(hash_key).encode().decode('unicode_escape').encode("raw_unicode_escape")[2:-1])
    return Response(content=value, status_code=200)


@app.post("/", response_model=None, response_class=Response)
async def poster(request: Request) -> Response: # type: ignore
    text = await request.body() # plan to save raw text as is in the database
    return Response(content=zlib.compress(text, level=9), status_code=200)

@app.post("/uncompress", response_model=None, response_class=Response)
async def poster(request: Request) -> Response: # type: ignore
    text = await request.body() # plan to save raw text as is in the database
    return Response(content=text.decode(), status_code=200)

@app.post("/brotli", response_model=None, response_class=Response)
async def poster(request: Request): # type: ignore
    text = await request.body() # plan to save raw text as is in the database
    hash = hashfunc()
    redis.set(hash, brotli.compress(text, quality=11))
    return Response(content=f"http://localhost:8010/{hash}", status_code=200)


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