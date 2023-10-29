from archlinux_discord.config import get_config
import logging
import requests
import os
import json


CACHE_FILE = ".cache.json"


def get_current_version(branch):
    if branch not in ["canary", "ptb", "stable"]:
        raise ValueError("Invalid branch")
    url = f"https://discord.com/api/updates/{branch}?platform=linux"
    logging.debug(f"Getting current version from {url}")
    resp = requests.get(url)
    if resp.status_code != 200:
        raise ValueError(f"Could not get current version: {resp.status_code}")
    data = resp.json()
    return data["name"]


def get_cached_version(branch):
    if branch not in ["canary", "ptb", "stable"]:
        raise ValueError("Invalid branch")
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
    return data.get(branch)


def set_cached_version(branch, version):
    if branch not in ["canary", "ptb", "stable"]:
        raise ValueError("Invalid branch")
    data = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
    data[branch] = version
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


def update_available(branch):
    if locked(branch):
        return None
    cached = get_cached_version(branch)
    current = get_current_version(branch)
    return current if cached != current else None


def locked(branch):
    data = {}
    if os.path.exists(".lockout.json"):
        with open(".lockout.json", "r") as f:
            data = json.load(f)
    return data.get(branch, False)


def lockout(branch):
    data = {}
    if os.path.exists(".lockout.json"):
        with open(".lockout.json", "r") as f:
            data = json.load(f)
    data[branch] = True
    with open(".lockout.json", "w") as f:
        json.dump(data, f)


def unlock(branch):
    data = {}
    if os.path.exists(".lockout.json"):
        with open(".lockout.json", "r") as f:
            data = json.load(f)
    del data[branch]
    with open(".lockout.json", "w") as f:
        json.dump(data, f)


def send_webhook_message(message):
    webhooks = get_config().get("webhooks")
    logging.debug(f"Sending webhook message: {message}: {webhooks}")
    for webhook_url in webhooks:
        logging.debug(f"Sending webhook message to {webhook_url}")
        res = requests.post(webhook_url, json={"content": message})
        res.raise_for_status()
