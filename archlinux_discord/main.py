import argparse
import logging
import os
import shutil
import time

from archlinux_discord.config import get_config, load_config
from archlinux_discord.discord import (lockout, send_webhook_message,
                                       set_cached_version, unlock,
                                       update_available)
from archlinux_discord.package import build_package
from archlinux_discord.repo import add_to_repo


def setup_logging(debug=False):
    logging.basicConfig(
        format="%(asctime)s [%(levelname)-5.5s]  %(message)s",
        level=logging.DEBUG if debug else logging.INFO,
    )


def auto(daemon=False):
    logging.info("Running in auto mode")

    if daemon:
        logging.info("Running in daemon mode")
        while True:
            for branch in ["canary", "ptb", "stable"]:
                check_for_updates(branch)
            logging.info("Next check in 60 seconds...")
            time.sleep(60)

    for branch in ["canary", "ptb", "stable"]:
        check_for_updates(branch)


def clean():
    logging.info("Cleaning all")
    shutil.rmtree(get_config().get("workdir"), ignore_errors=True)
    try:
        os.remove(".cache.json")
    except FileNotFoundError:
        pass


def check_for_updates(branch):
    logging.info("Checking for updates for %s", branch)
    new_version = update_available(branch)
    if new_version:
        logging.info("New version available: %s", new_version)
        send_webhook_message(
            f"New {branch} version available: {new_version}. Initiating build"
        )
        built_package = build_package(branch, new_version)
        logging.info("Built package: %s", built_package)
        if not build_package:
            lockout(branch)
            send_webhook_message(
                f":rotating_light: Build failed for {branch} and {new_version}. Builds will not be attempted for this channel"
            )
            return
        add_to_repo(built_package)
        set_cached_version(branch, new_version)
        send_webhook_message(f"{branch} {new_version} built and added to repo")
    else:
        logging.info("No new version available")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", default=False)
    parser.add_argument(
        "--branch",
        choices=["canary", "ptb", "stable"],
        default=None,
    )
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--unlock", action="store_true", default=False)
    parser.add_argument("--lock", action="store_true", default=False)
    parser.add_argument("--daemon", action="store_true", default=False)
    args = parser.parse_args()
    setup_logging(args.debug)
    load_config()

    if args.clean:
        clean()
    elif args.branch:
        if args.unlock:
            logging.info("Unlocking %s", args.branch)
            unlock(args.branch)
        elif args.lock:
            logging.info("Locking %s", args.branch)
            lockout(args.branch)
        else:
            check_for_updates(args.branch)
    else:
        auto(args.daemon)


if __name__ == "__main__":
    main()
