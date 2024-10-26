#!/usr/bin/env python3

import argparse
import inspect
import json
import os
import shutil
import stat
import sys
import webbrowser
from dataclasses import dataclass
from zipfile import ZipFile

import requests
from colorama import Fore, just_fix_windows_console
from platformdirs import user_config_dir

from . import solve

just_fix_windows_console()


@dataclass
class Config:
    contest_id: str
    session_cookie: str
    xsrf_token: str
    solve_template_filename: str | None


CONFIG_DIR = user_config_dir("ccc")
CONFIG_FILE = os.path.join(CONFIG_DIR, "ccc.json")
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)
if not os.path.exists(os.path.join(CONFIG_DIR, "solve")):
    open(os.path.join(CONFIG_DIR, "solve"), "w").write(inspect.getsource(solve))
CONFIG = Config("", "", "", "")


def try_get_config():
    global CONFIG
    if not os.path.exists(CONFIG_FILE):
        print("Could not find config file, please run `ccc setup`")
        sys.exit(1)
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        CONFIG = Config(**data)


def check_api_authentication():
    url = "https://catcoder.codingcontest.org/api/public/user/current"
    headers = {
        "cookie": f"SESSION={CONFIG.session_cookie}; XSRF-TOKEN={CONFIG.xsrf_token}",
    }
    current_user = None
    try:
        response = requests.get(url, headers=headers)
        current_user = response.json()["username"]
    except Exception as _:
        print("Could not authenticate, please run `ccc setup`")
        sys.exit(1)
    assert current_user
    print(f"Logged in as {current_user}")


def set_config(contest_id, session_cookie, xsrf_token, solve_template_filename=None):
    CONFIG.contest_id = contest_id
    CONFIG.session_cookie = session_cookie
    CONFIG.xsrf_token = xsrf_token
    if solve_template_filename:
        CONFIG.solve_template_filename = solve_template_filename
    else:
        CONFIG.solve_template_filename = os.path.join(CONFIG_DIR, "solve")
    with open(CONFIG_FILE, "w") as f:
        json.dump(CONFIG.__dict__, f)


def get_level() -> int:
    """Returns the level we are at for the current contest."""
    url = f"https://catcoder.codingcontest.org/api/game/level/{CONFIG.contest_id}"
    headers = {
        "cookie": f"SESSION={CONFIG.session_cookie}; XSRF-TOKEN={CONFIG.xsrf_token}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Error getting level, please run setup first")
        sys.exit(1)
    current_level = response.json()["currentLevel"]
    return current_level


def get_input_zip() -> bytes:
    """Gets the zip with the inputs for the current level of the current contest."""
    url = f"https://catcoder.codingcontest.org/api/contest/{CONFIG.contest_id}/file-request/input"
    headers = {
        "cookie": f"SESSION={CONFIG.session_cookie}; XSRF-TOKEN={CONFIG.xsrf_token}",
    }
    response = requests.get(url, headers=headers)
    zip_url = response.json()["url"]
    zip_response = requests.get(zip_url, headers=headers)
    zip_contents = zip_response.content
    return zip_contents


def get_description_url() -> str:
    """Gets the URL for the PDF containing the description of the current level of the current contest."""
    url = f"https://catcoder.codingcontest.org/api/contest/{CONFIG.contest_id}/file-request/description"
    headers = {
        "cookie": f"SESSION={CONFIG.session_cookie}; XSRF-TOKEN={CONFIG.xsrf_token}",
    }
    response = requests.get(url, headers=headers)
    description_url = response.json()["url"]
    return description_url


def generate_files():
    """Sets up the inputs and template, and opens the problem description for a new level. Run this from the contest's root directory."""
    level = str(get_level())
    print(f"Level {level}")
    if os.path.exists(f"{level}"):
        print(f"Level {level} already exists")
        sys.exit(0)

    description_url = get_description_url()
    if webbrowser.get():
        print("Opening level description")
        webbrowser.open_new_tab(description_url)
    else:
        print(f"Level description URL: {description_url}")

    print("Creating directories")
    os.mkdir(f"{level}")
    os.mkdir(os.path.join(level, "in"))
    os.mkdir(os.path.join(level, "out"))

    print("Creating solve template")
    with open(os.path.join(level, "solve"), "wb") as f:
        assert CONFIG.solve_template_filename
        template_contents = open(CONFIG.solve_template_filename, "rb").read()
        f.write(template_contents)
    st = os.stat(os.path.join(level, "solve"))
    os.chmod(os.path.join(level, "solve"), st.st_mode | stat.S_IEXEC)

    print("Downloading input files")
    input_zip = get_input_zip()
    with open(os.path.join(level, "in", "input.zip"), "wb") as f:
        f.write(input_zip)

    with ZipFile(os.path.join(level, "in", "input.zip"), "r") as z:
        z.extractall(os.path.join(level, "in"))
    if shutil.which("git"):
        print("Setting up git repository")
        os.system(f"git init {level} --quiet")
        os.chdir(os.path.join(os.getcwd(), level))
        os.system("git add *")
        os.system("git commit -m 'initial commit' --quiet")
    print("Done")


def submit_code(level):
    url = f"https://catcoder.codingcontest.org/api/game/{CONFIG.contest_id}/{level}/upload"
    headers = {
        "cookie": f"SESSION={CONFIG.session_cookie}; XSRF-TOKEN={CONFIG.xsrf_token}",
    }
    if not os.path.exists("solve"):
        print("No `solve` file found in the current directory")
        sys.exit(1)
    res = requests.post(
        url,
        headers=headers,
        files={"file": ("solve", open("solve", "rb"), "text")},
    )
    if res.ok:
        print("Code successfully uploaded")
    else:
        print("Something went wrong when uploading the code")
        sys.exit(1)


def submit():
    """Grabs the .out files from the current working directory and submits them. Run this from the level directory."""
    URL = f"https://catcoder.codingcontest.org/api/game/{CONFIG.contest_id}/upload/solution/"
    level = get_level()
    if os.path.basename(os.path.normpath(os.getcwd())) != str(level):
        print(f"Not running in the current level ({level}) directory")
        sys.exit(1)

    print(f"Submitting level {level}")
    headers = {
        "cookie": f"SESSION={CONFIG.session_cookie}; XSRF-TOKEN={CONFIG.xsrf_token}",
    }
    if not any(file.endswith(".out") for file in os.listdir("out")):
        print("No .out files found in the `out` directory! Run the solve script first.")
        sys.exit(1)
    for file in list(sorted(os.listdir("out"))):
        if file.endswith(".out") and "example" not in file:
            fn = file.replace(".out", "")
            res = requests.post(
                URL + fn,
                headers=headers,
                files={"file": open(os.path.join("out", file), "rb")},
            )
            res = res.json()
            res = res["results"].get(fn)
            if res == "VALID":
                print(Fore.GREEN + f"✅{fn}")
            else:
                print(Fore.RED + f"❌{fn}")
                sys.exit(1)
    print("All submissions accepted!")
    print("Upload code? [y/n] ", end="")
    if input().strip().lower() == "y":
        submit_code(level)


def main():
    parser = argparse.ArgumentParser(
        description="CatCoder CLI for the Cloudflight Coding Contest"
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    setup_parser = subparsers.add_parser("setup")
    setup_parser.add_argument("contest_id", type=int, help="Contest ID")
    setup_parser.add_argument("session_cookie", type=str, help="Session cookie")
    setup_parser.add_argument(
        "xsrf_token", type=str, help="XSFR token", nargs="?", default=""
    )
    setup_parser.add_argument(
        "solve_template_filename",
        type=str,
        help="Path to the solve file template. By default, uses a Python template will be used",
        nargs="?",
        default=None,
    )

    subparsers.add_parser("gen")

    subparsers.add_parser("submit")

    # call function according to chosen subcommand
    args = parser.parse_args()
    if args.subcommand not in ("setup", "gen", "submit"):
        parser.print_help()
        sys.exit(1)

    if args.subcommand == "setup":
        set_config(
            args.contest_id,
            args.session_cookie,
            args.xsrf_token,
            args.solve_template_filename,
        )
    else:
        try_get_config()
    check_api_authentication()
    if args.subcommand == "gen":
        generate_files()
    if args.subcommand == "submit":
        submit()
