import logging
import os
import shutil
import subprocess
from archlinux_discord.config import get_config


def build_package(branch: str, version: str):
    logging.info(f"Building branch {branch} with version {version}")
    path = os.path.join(get_config().get("workdir"), branch)
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
    ret = subprocess.run("updpkgsums", shell=True, cwd=path)
    if ret.returncode != 0:
        logging.error("Could not update checksums")
        logging.error(ret.stderr)
        return None
    logging.debug(f"Building package...")
    ret = subprocess.run(
        "makepkg -sf --noconfirm",
        shell=True,
        cwd=path,
        env={"PACKAGER": "Arch Linux Discord <mrkirby153@mrkirby153.com>"},
    )
    if ret.returncode != 0:
        logging.error("Could not build package")
        logging.error(ret.stderr)
        return None
    logging.info("Package built successfully!")
    for file in os.listdir(path):
        if file.endswith(".pkg.tar.zst"):
            return os.path.join(path, file)
