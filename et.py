import json
import os
import subprocess
import sys
import urllib.request as urllib
from time import sleep
from urllib.error import HTTPError


def exit(message):
    print(message)
    sys.exit(1)


def require(varname, default=None):
    return os.getenv(varname, default) or exit(f"error: {varname} environment variable missing")


CF_USERNAME = require("CF_USERNAME")
CF_KEY = require("CF_KEY")
CF_DOMAIN = require("CF_DOMAIN")
CF_SUBDOMAIN = require("CF_SUBDOMAIN")


def request(path, method="GET", headers=None, data=None):
    headers = headers or {}
    headers["x-auth-email"] = CF_USERNAME
    headers["x-auth-key"] = CF_KEY

    if data is not None:
        headers["content-type"] = "application/json"

    request = urllib.Request(
        f"https://api.cloudflare.com/client/v4/{path.lstrip('/')}",
        method=method,
        headers=headers or {},
        data=data and json.dumps(data).encode("utf-8")
    )

    with urllib.urlopen(request) as resp:
        return json.load(resp)


def getip():
    with urllib.urlopen("https://api.ipify.org?format=json") as resp:
        return json.load(resp)["ip"]


while True:
    try:
        ipaddr = getip()
        zone = request(f"/zones?name={CF_DOMAIN}")["result"][0]
        records = request(f"/zones/{zone['id']}/dns_records")["result"]
        for record in records:
            if record["type"] == "A" and record["name"] == CF_SUBDOMAIN:
                break
        else:
            record = None

        record_data = {
            "type": "A",
            "name": CF_SUBDOMAIN,
            "content": ipaddr,
            "proxied": False,
        }

        if record is None:
            request(
                f"/zones/{zone['id']}/dns_records",
                data=record_data,
                method="POST",
            )
        else:
            request(
                f"/zones/{zone['id']}/dns_records/{record['id']}",
                data=record_data,
                method="PUT",
            )

    except HTTPError as e:
        print(f"error: {e}")
        try:
            print(json.load(e))
        except Exception as e:
            print("error reading response: {e}")

    except Exception as e:
        print(f"error: {e}")

    finally:
        sleep(3600 * 1)
