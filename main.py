"""
Python App to retrieve F5 Poolmember information from Redis DB
and return information in either a svg image or a json format
"""
import logging
import os
import redis
from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI, Path, Request
from fastapi.responses import Response, HTMLResponse
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv
from lbredis.redis_client import redis_client
from telemetry.telemetry_functions import generate_telemetry


logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)


# Variables
TITLE = "F5 Poolmember Dashboard API 🚀"
DESCRIPTION = "Endpoint get F5 Poolmember related information"
GITHUB_REPO = "https://github.com/jbollineni/f5-poolmember-dashboard"

load_dotenv()
REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


# Call Redis Client to subsribe and update DB
# redis_client(REDIS_ENDPOINT, REDIS_PASSWORD)

# Redis connection objects
# DB1 stores pool information, populated by a redis python client 
# which gets data from Vector
rconn_pool = redis.StrictRedis(
    host=REDIS_ENDPOINT,
    port=6379,
    password=REDIS_PASSWORD,
    db=1,
    decode_responses=True,
)
# DB2 stores GSLB WIP related details
rconn_wip = redis.StrictRedis(
    host=REDIS_ENDPOINT,
    port=6379,
    password=REDIS_PASSWORD,
    db=2,
    decode_responses=True,
)
# DB2 stores SLB VIP related details
rconn_vip = redis.StrictRedis(
    host=REDIS_ENDPOINT,
    port=6379,
    password=REDIS_PASSWORD,
    db=3,
    decode_responses=True,
)

# Instantiate FastAPI
app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Set Home Page
with open("./homepage.html.j2", encoding="utf-8") as file:
    HOME_PAGE = file.read().format(
        TITLE=TITLE, DESCRIPTION=DESCRIPTION, GITHUB_REPO=GITHUB_REPO
    )


# Return About page
@app.get(
    path="/",
    summary="Home page",
    description=DESCRIPTION,
    response_class=HTMLResponse,
    responses={200: {"content": {"text/html": {"schema": None}}}},
)
def root():
    return HTMLResponse(content=HOME_PAGE, status_code=200, media_type="text/html")


# Return output in svg (tablular) format
@app.get("/status/{objectType}/{objectName}/json")
@app.get("/status/{objectType}/{objectName}/image.svg")
@app.get("/status/{objectType}/{objectName}")
def get_lb_object(
    request: Request,
    objectType: str,
    objectName: str = Path(
        default=..., min_length=5, max_length=30, example="vs_exampleapp-1p_80 or exampleapp.gslb.example.net or p_exampleapp-1p_80"
    ),
):
    lb_name = "bigip01a.example.net"

    if objectType == "slbvip":
        objectType = "SLB VIP"
        rconn_parent_object = rconn_vip

    elif objectType == "gslbwip":
        objectType = "GSLB WIP"
        rconn_parent_object = rconn_wip

    print(request.url.path)

    if request.url.path.endswith("/json"):
        output_json = generate_telemetry(
            rconn_pool, rconn_parent_object, lb_name, objectType, objectName, "json"
        )
        return Response(content=output_json, media_type="application/json")
    else:
        output_svg = generate_telemetry(
            rconn_pool, rconn_parent_object, lb_name, objectType, objectName, "image"
        )
        # response.headers["Content-Type"] = "image/svg+xml"
        return Response(content=output_svg, media_type="image/svg+xml")
