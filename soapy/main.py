from hashing import hashfunc
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response

from dotenv import load_dotenv
import httpx
import os
import datetime
import psutil
import sys

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


@app.on_event("startup")
def startup():
    load_dotenv()


@app.get("/", response_model=None, response_class=Response)
async def getter() -> Response:  # type: ignore
    return HTMLResponse(content="Hello world!", status_code=200)


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
        "bind": "0.0.0.0:8000",
        "workers": len(psutil.Process().cpu_affinity()),  # type: ignore
        "accesslog": "-",
        "errorlog": "-",
        "worker_class": "uvicorn.workers.UvicornWorker",
        "logger_class": StubbedGunicornLogger,
        "reload": "True",
        "reload_engine": "inotify",  # requires inotify package
    }

    StandaloneApplication("main:app", options).run()
