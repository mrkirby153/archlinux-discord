import logging
import os
import shutil
import subprocess
from archlinux_discord.config import get_config


def archive_old_package(name):
    REPO_LOCATION = get_config().get("repo_location")
    logging.debug("Archiving old package...")
    archive_path = os.path.join(REPO_LOCATION, "archive", name)
    old_file = os.path.join(REPO_LOCATION, name)
    if not os.path.exists(old_file):
        logging.debug("Old package does not exist")
        return

    if os.path.exists(archive_path):
        logging.debug("Removing existing archive...")
        shutil.rmtree(archive_path)
    os.makedirs(archive_path, exist_ok=True)
    os.rename(os.path.join(REPO_LOCATION, name), os.path.join(archive_path, name))
    if os.path.exists(os.path.join(REPO_LOCATION, name + ".sig")):
        os.rename(
            os.path.join(REPO_LOCATION, name + ".sig"),
            os.path.join(archive_path, name + ".sig"),
        )


def remove_old_files():
    REPO_LOCATION = get_config().get("repo_location")
    logging.debug("Removing old files...")
    for file in os.listdir(REPO_LOCATION):
        if file.endswith(".old") or file.endswith(".old.sig"):
            logging.debug(f"Removing {file}")
            os.remove(os.path.join(REPO_LOCATION, file))


def add_to_repo(path):
    REPO_LOCATION = get_config().get("repo_location")
    SIGNING_KEY = get_config().get("signing_key")
    os.makedirs(REPO_LOCATION, exist_ok=True)
    logging.debug("Copying package to repo...")
    dest = os.path.join(REPO_LOCATION, os.path.basename(path))
    shutil.copyfile(path, dest)
    if SIGNING_KEY:
        logging.info("Signing package...")
        existing_signature = os.path.exists(dest + ".sig")
        if existing_signature:
            logging.debug("Removing existing signature...")
            os.remove(dest + ".sig")

        ret = subprocess.run(
            [
                "gpg",
                "--sign",
                "--detach-sign",
                f"--default-key={SIGNING_KEY}",
                os.path.basename(path),
            ],
            cwd=REPO_LOCATION,
        )
        if ret.returncode != 0:
            logging.error("Could not sign package")
            logging.error(ret.stderr)
            return None
    logging.debug("Updating repo database...")

    repo_add_cmd = ["repo-add"]
    if SIGNING_KEY:
        repo_add_cmd.append("-s")
        repo_add_cmd.append("-k")
        repo_add_cmd.append(SIGNING_KEY)
    repo_add_cmd.append("discord.db.tar.gz")
    repo_add_cmd.append(os.path.basename(path))

    ret = subprocess.run(
        repo_add_cmd,
        cwd=REPO_LOCATION,
    )
    if ret.returncode != 0:
        logging.error("Could not add package to repo")
        logging.error(ret.stderr)
        return None
    remove_old_files()
