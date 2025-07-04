import shutil
import logging
import os
import time
from archlinux_discord.package import build_package
from archlinux_discord.repo import add_to_repo, archive_old_package
from archlinux_discord.config import load_config, get_config
from archlinux_discord.discord import (
    update_available,
    send_webhook_message,
    set_cached_version,
    lockout,
    unlock,
    get_cached_file_name,
    set_cached_file_name,
)

import argparse


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
    logging.info(f"Checking for updates for {branch}")
    new_version = update_available(branch)
    if new_version:
        logging.info(f"New version available: {new_version}")
        send_webhook_message(
            f"New {branch} version available: {new_version}. Initiating build"
        )
        built_package = build_package(branch, new_version)
        logging.info(f"Built package: {built_package}")
        if not built_package:
            lockout(branch)
            send_webhook_message(
                f":rotating_light: Build failed for {branch} and {new_version}. Builds will not be attempted for this channel"
            )
            return
        old_package = get_cached_file_name(branch)
        logging.info(f"Old package: {old_package}")
        if old_package:
            archive_old_package(old_package)
        add_to_repo(built_package)
        set_cached_version(branch, new_version)
        set_cached_file_name(branch, os.path.basename(built_package))
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
            logging.info(f"Unlocking {args.branch}")
            unlock(args.branch)
        elif args.lock:
            logging.info(f"Locking {args.branch}")
            lockout(args.branch)
        else:
            check_for_updates(args.branch)
    else:
        auto(args.daemon)


if __name__ == "__main__":
    main()
