import logging
import os
import shutil
import subprocess
import shlex
from archlinux_discord.config import get_config


def _run_with_timeout(cmd, timeout=300, **kwargs):
    proc = subprocess.Popen(cmd, **kwargs)
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        logging.error(f"Command {cmd} timed out")
        proc.kill()
        return None
    if proc.returncode != 0:
        logging.error(f"Command {cmd} returned non-zero exit code")
        return None
    return proc


def build_package(branch: str, version: str):
    logging.info(f"Building branch {branch} with version {version}")
    path = os.path.join(get_config().get("workdir"), branch)

    if os.path.exists(path):
        logging.info(f"Removing existing working directory {path}")
        shutil.rmtree(path)

    os.makedirs(path, exist_ok=True)

    logging.debug(f"Copying PKGBUILD to working directory...")
    shutil.copyfile(
        os.path.join(get_config().get("pkgbuild_dir"), f"PKGBUILD.{branch}"),
        os.path.join(path, "PKGBUILD"),
    )
    logging.debug(f"Replacing version in PKGBUILD...")
    ret = subprocess.run(
        f"sed -i 's/pkgver=.*/pkgver={version}/' PKGBUILD", shell=True, cwd=path
    )
    if ret.returncode != 0:
        logging.error("Could not replace version in PKGBUILD")
        logging.error(ret.stderr)
        return None

    logging.debug(f"Updating checksums...")
    if not _run_with_timeout("updpkgsums", shell=True, cwd=path):
        logging.error("Could not update checksums")
        return None
    logging.debug(f"Building package...")
    if not _run_with_timeout(
        "extra-x86_64-build",
        shell=True,
        cwd=path,
        env={"PACKAGER": "Arch Linux Discord <mrkirby153@mrkirby153.com>"},
    ):
        logging.error("Could not build package")
        return None
    logging.info("Package built successfully!")
    for file in os.listdir(path):
        if file.endswith(".pkg.tar.zst"):
            return os.path.join(path, file)
