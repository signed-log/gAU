# /usr/bin/env python3

import os
import argparse
import sys
import logging
import hashlib
import re
import subprocess
from pathlib import Path, PurePath
from git.objects import tag

import requests as curl
from git import Repo

parser = argparse.ArgumentParser(description="Check update for (and auto-update) github release-based AUR packages")
parser.add_argument(
    "maintainer",
    type=str,
    nargs=1,
    default=None,
    help="Your maintainer name in the AUR",
)
parser.add_argument(
    "-a",
    "--auto",
    action="store_true",
    dest="auto",
    default=False,
    help="Auto updates release",
)
parser.add_argument(
    "-n",
    "--dry-run",
    action="store_true",
    dest="dry",
    default=False,
    help="Does a dry-run",
)
"""
parser.add_argument(
    "--verbose",
    "-v",
    action="count",
    dest="verbose",
    # 0 = WARNING
    # 1 = INFO
    # 2 = DEBUG
    default=0
)
arg.quiet = -arg.quiet
loglevel = arg.verbose + arg.quiet
"""


def initlogging():
    """Initialise logging"""
    log_path = PurePath(os.getcwd() + "aurupdate.log")
    if "aurupdate.log" not in os.listdir():
        log_path.touch()
    logging.basicConfig(filename=str(log_path), encoding="utf-8")


dir = "/home/stig124/dev/packaging/aur"
api_url = "https://aur.archlinux.org/rpc/"


def md5(fileh):
    with open(f"{dir}/{fileh}/PKGBUILD", "rb") as f:
        data = f.read()
        hashr = hashlib.md5(data).hexdigest()
        return hashr


def search_string_in_file(file_name: str, string_to_search: str):
    """Search for a string in file

    Args:
        file_name (str): Path of the file to use
        string_to_search (str): String to search in that file

    Returns:
        list: List of the results with line number
    """
    line_number = 0
    list_of_results = []
    with open(file_name, "r") as read_obj:
        for line in read_obj:
            line_number += 1
            if string_to_search in line:
                list_of_results.append((line_number, line.rstrip()))
    return list_of_results


def getpackages(path):
    """Extract github link from the PKGBUILD source line

    Args:
        path (str): Path of the PKGBUILD

    Returns:
        str: Link
    """
    try:
        matched_lines = dict(search_string_in_file(path, "github.com"))
    except FileNotFoundError or TypeError:
        return None
    else:
        os.chdir(path)
        if "source" in matched_lines:
            for i, n in matched_lines.items():
                if "source" in n:
                    regex = re.compile("((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)")
                    link = (str(re.search(regex, n).group()).rstrip("$").lstrip("https://"))
                    return link


def parsegh(link: str):
    """P

    Args:
        link (str): Extracted link

    Returns:
        str: latest tag
    """
    link2 = link.strip("/")
    owner = link2[1]
    repo = link2[2]
    release = getreleasegh(owner=owner, repo=repo)
    return release


def getreleasegh(owner: str, repo: str, search="tags"):
    """Fetch the latest tag in the github repo

    Args:
        owner (str): Owner of the repo
        repo (str): Repo name
        search (str, optional): What to search in the github API. Defaults to "tags".

    Returns:
        str: latest tag
    """
    url = "https://api.github.com/repos/" + owner + repo + search
    with curl.get(url) as r:
        if r.status_code == 200:
            j = r.json()
    release = str(j[0]["name"])
    tag_history = j
    return release, tag_history


def parserepo(tag_history, outdated_vname):
    lst = []
    for i in range(len(tag_history)):
        pass

if __name__ == "__main__":
    arg = parser.parse_args()
    initlogging()
    try:
        contents = os.listdir(dir)
    except PermissionError:
        logging.critical(f"You don't have acess to {dir}")
        sys.exit()
    else:
        for i in contents:
            path = [f"{dir}/{i}/PKGBUILD" if "PKGBUILD" in os.listdir(f"{dir}/{i}") else None]
            rcode = getpackages(path=path)
            if rcode is None or not type(str):
                logging.info(f"Folder {path} doesn't contain a PKGBUILD")
                break
            else:
                release = parsegh(rcode)
                actual_version = dict(search_string_in_file(path, "pkgver="))
                actual_version2, *_ = actual_version.values()
                actual_version2 = actual_version2.split("=")[1]
