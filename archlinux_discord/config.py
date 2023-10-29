import json
import logging
import os

config = {
    "signing_key": None,
    "repo_location": "repo",
    "pkgbuild_dir": "pkgbuilds",
    "workdir": ".workdir",
    "webhooks": [],
}


def get_config():
    return config


def load_config():
    global config
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            loaded_config = json.load(f)
            logging.debug(f"Loaded config: {loaded_config}")
            config = {**config, **loaded_config}
            logging.info("Loaded config from config.json")
    logging.debug(f"Configuration: {config}")
