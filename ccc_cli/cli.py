#!/usr/bin/env python3

import argparse
import json
import os
import sys

import requests

# solve template
TEMPLATE = r"""
import os
import sys

# ===========================================================================================================
# Solve
# ==========================================================================================================


# input: lines of the input file
# returns: the result as a string
def solve(input: list[str]) -> str:
    res = ""
    return res


# ===========================================================================================================
# Main
# ===========================================================================================================

if __name__ == "__main__":
    run = False
    test = False

    if len(sys.argv) < 2:
        run = True
        test = True
    elif sys.argv[1] == "run":
        run = True
    elif sys.argv[1] == "test":
        test = True

    if test:
        print("Running on example input")
        OKGREEN = "\033[92m"
        FAIL = "\033[91m"
        ENDC = "\033[0m"
        for file in os.listdir("in"):
            if file.endswith(".in") and "example" in file:
                with open(f"in/{file}", "r") as f:
                    input = f.readlines()
                    res = str(solve(input))
                with open(f"in/{file[:-3]}.out", "r") as f:
                    expected = f.read()
                if res.strip() == expected.strip():
                    print(OKGREEN + "✅" + f"{file} accepted" + ENDC)
                else:
                    print(FAIL + "❌" + f"{file} failed" + ENDC)
                    print()
                    print(f"Got:\n{res}")
                    print()
                    print(f"Expected:\n{expected}")
                    sys.exit(1)
    if test and run:
        print()
    if run:
        print("Running on regular inputs")
        for file in sorted(os.listdir("in")):
            if file.endswith(".in"):
                with open(f"in/{file}", "r") as f:
                    input = f.readlines()
                    res = str(solve(input))
                    print(f"{file} done")
                with open(f"out/{file[:-3]}.out", "w") as f:
                    f.write(res)
"""


class bcolors:
    """Terminal escape codes to display colors."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    SKIP = "\033[37m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def setup(contest_id=None, session_cookie=None, xsrf_token=None):
    """Sets up the CLI.

    If arguments are passed, it saves them to the ~/.ccc.json file.
    If no arguments are passed, it reads them from the ~/.ccc.json file.
    """
    global CONTEST_ID, SESSION_COOKIE, XSRF_TOKEN
    if contest_id is None:
        try:
            with open(os.path.expanduser("~/.ccc.json"), "r") as f:
                data = json.load(f)
                CONTEST_ID = data["contest_id"]
                SESSION_COOKIE = data["session_cookie"]
                XSRF_TOKEN = data["xsrf_token"]
        except FileNotFoundError:
            print("Run 'ccc setup' first")
            sys.exit(1)
    else:
        with open(os.path.expanduser("~/.ccc.json"), "w") as f:
            json.dump(
                {
                    "contest_id": contest_id,
                    "session_cookie": session_cookie,
                    "xsrf_token": xsrf_token,
                },
                f,
            )


def get_level() -> str:
    """Returns the level we are at for the current contest."""
    URL = f"https://catcoder.codingcontest.org/api/game/level/{CONTEST_ID}"
    headers = {
        "cookie": f"SESSION={SESSION_COOKIE}; XSRF-TOKEN={XSRF_TOKEN}",
    }
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print("Error getting level, please run setup first")
        sys.exit(1)
    current_level = response.json()["currentLevel"]
    return current_level


def get_input():
    """Gets the zip with the inputs for the current level of the current contest."""
    URL = f"https://catcoder.codingcontest.org/api/contest/{CONTEST_ID}/file-request/input"
    headers = {
        "cookie": f"SESSION={SESSION_COOKIE}; XSRF-TOKEN={XSRF_TOKEN}",
    }
    response = requests.get(URL, headers=headers)
    zip_url = response.json()["url"]
    response = requests.get(zip_url, headers=headers)
    return response.content


def get_description_url() -> str:
    """Gets the URL for the PDF containing the description of the current level of the current contest."""
    URL = f"https://catcoder.codingcontest.org/api/contest/{CONTEST_ID}/file-request/description"
    headers = {
        "cookie": f"SESSION={SESSION_COOKIE}; XSRF-TOKEN={XSRF_TOKEN}",
    }
    response = requests.get(URL, headers=headers)
    url = response.json()["url"]
    return url


def gen():
    """Sets up the inputs and template, and opens the problem description for a new level. Run this from the contest's root directory."""
    level = get_level()
    print(f"Level {level}")
    if os.path.exists(f"{level}"):
        print(f"Level {level} already exists")
        sys.exit(0)

    print("Opening description")
    description_url = get_description_url()
    os.system(f"google-chrome '{description_url}'")

    print("Creating directories")
    os.mkdir(f"{level}")
    os.mkdir(f"{level}/in")
    os.mkdir(f"{level}/out")

    print("Creating template file")
    with open(f"{level}/solve.py", "w") as f:
        f.write(TEMPLATE)

    print("Downloading input files")
    input_zip = get_input()
    with open(f"{level}/in/input.zip", "wb") as f:
        f.write(input_zip)

    os.system(f"unzip {level}/in/input.zip -d {level}/in")
    os.system(f"git init {level}")
    os.system(f"cd {level} && git add * && git commit -m 'initial commit' && cd ..")
    print("Done")


def submit_code(level):
    URL = f"https://catcoder.codingcontest.org/api/game/{CONTEST_ID}/{level}/upload"
    headers = {
        "cookie": f"SESSION={SESSION_COOKIE}; XSRF-TOKEN={XSRF_TOKEN}",
    }
    if not os.path.exists("solve.py"):
        print("No solve.py found in the current directory")
        sys.exit(1)
    res = requests.post(
        URL,
        headers=headers,
        files={"file": ("solve.py", open("solve.py", "rb"), "text/x-python")},
    )
    if res.ok:
        print("Code successfully uploaded")
    else:
        print("Something went wrong when uploading the code")
        sys.exit(1)


def submit():
    """Grabs the .out files from the current working directory and submits them. Run this from the level directory."""
    URL = f"https://catcoder.codingcontest.org/api/game/{CONTEST_ID}/upload/solution/"
    level = get_level()
    if os.getcwd().split("/")[-1] != str(level):
        print(f"Not running in the current level ({level}) directory")
        sys.exit(1)

    print(f"Submitting level {level}")
    headers = {
        "cookie": f"SESSION={SESSION_COOKIE}; XSRF-TOKEN={XSRF_TOKEN}",
    }
    if not any(file.endswith(".out") for file in os.listdir("out")):
        print('No .out files found in the "out" directory! Run the solve script first.')
        sys.exit(1)
    for file in list(sorted(os.listdir("out"))):
        if file.endswith(".out") and "example" not in file:
            fn = file.replace(".out", "")
            res = requests.post(
                URL + fn, headers=headers, files={"file": open(f"out/{file}", "rb")}
            )
            res = res.json()
            res = res["results"].get(fn)
            if res == "VALID":
                print(bcolors.OKGREEN + "✅" + fn + bcolors.ENDC)
            else:
                print(bcolors.FAIL + "❌" + fn + bcolors.ENDC)
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
    setup_parser.add_argument("xsrf_token", type=str, help="XSFR token")

    subparsers.add_parser("gen")

    subparsers.add_parser("submit")

    # call function according to chosen subcommand
    args = parser.parse_args()
    if args.subcommand not in ("setup", "gen", "submit"):
        parser.print_help()
        sys.exit(1)

    if args.subcommand == "setup":  # save new values
        setup(
            contest_id=args.contest_id,
            session_cookie=args.session_cookie,
            xsrf_token=args.xsrf_token,
        )
    else:  # grab cached values instead
        setup()
    if args.subcommand == "gen":
        gen()
    if args.subcommand == "submit":
        submit()
