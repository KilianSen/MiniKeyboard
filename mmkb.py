import argparse
import os.path
import time

import requests

VERSION = 1  # version of the script, has to be on top of the file
UPDATE_URL = "https://raw.githubusercontent.com/username/repo/master/mmkb.py"


def get_key_info():
    parser = argparse.ArgumentParser()
    parser.add_argument("keyIndex", type=int)
    parser.add_argument("pressTime", type=float)
    args = parser.parse_args()
    return args.keyIndex, args.pressTime


def get_file_from_url(url):
    return requests.get(url).text


def update():
    # check value in update.lock
    if os.path.isfile("update.lock"):

        with open("update.lock", "r") as f:
            last_update = int(f.read())

            delta = time.time() - last_update

            if delta < 3600:
                print("Skipping update, last update check was less than an hour ago")
                return

    data = get_file_from_url(UPDATE_URL).split("\n")
    version_index = [line.startswith("VERSION=") for line in data].index(True)
    version = int(data[version_index].split("=")[1])

    if version <= VERSION:
        return

    # update the file
    with open(__file__, "w") as f:
        f.write("\n".join(data))

    with open("update.lock", "w") as f:
        f.write(str(int(time.time())))


if __name__ == "__main__":
    print(get_key_info())
    print("Checking for updates...")
    update()
