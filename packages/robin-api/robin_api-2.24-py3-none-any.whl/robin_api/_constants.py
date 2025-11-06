# File generated from our OpenAPI spec by Stainless.

import httpx

RAW_RESPONSE_HEADER = "X-Stainless-Raw-Response"

# default timeout is 10 minutes
DEFAULT_TIMEOUT = httpx.Timeout(timeout=1000.0, connect=5.0)
#DEFAULT_TIMEOUT = 600
DEFAULT_MAX_RETRIES = 2
DEFAULT_LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20)

""" DEFAULT_HEADERS = {
    "Content-Type": "application/json"
    } """
DEFAULT_HEADERS ={}