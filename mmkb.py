import argparse
import ctypes
import os.path
import time
from pathlib import Path

import requests

VERSION = 8  # version of the script, has to be on top of the file


def get_key_info():
    parser = argparse.ArgumentParser()
    parser.add_argument("keyIndex", type=int)
    parser.add_argument("pressTime", type=float)
    parser.add_argument("updateInterval", type=int)
    parser.add_argument("updateURL", type=str)
    args = parser.parse_args()
    return args.keyIndex, args.pressTime, args.updateInterval, args.updateURL


def get_file_from_url(url):
    return requests.get(url).text


def update(url: str, interval: int):
    # check value in update.lock
    if os.path.isfile(f"{Path(__file__).stem}.update.lock"):

        with open(f"{Path(__file__).stem}.update.lock", "r") as f:
            last_update = int(f.read())

            delta = time.time() - last_update

            if delta < interval * 60:
                return

    print("Checking for updates")

    with open(f"{Path(__file__).stem}.update.lock", "w") as f:
        f.write(str(int(time.time())))

    data = get_file_from_url(url).split("\n")
    version_index = int([line.startswith("VERSION") for line in data].index(True).__str__().strip())
    version = int(data[version_index].split("=")[1].split("#")[0].strip())

    if version <= VERSION:
        return

    # update the file
    with open(__file__, "w") as f:
        f.write("\n".join(data))


def mail():
    print("Opening Mail")
    os.system("start thunderbird")


def calc():
    print("Opening Calculator")
    os.system("calc")


def lock():
    print("Locking Screen")
    ctypes.windll.user32.LockWorkStation()

def shutdown():
    print("Shutting down")
    os.system("shutdown /s /t 1")


if __name__ == "__main__":
    k, t, update_interval, update_url = get_key_info()

    if t < 1:
        match k:
            case 1:
                mail()
            case 0:
                calc()
            case 2:
                lock()

    elif t > 5 < 10:
        match k:
            case 2:
                shutdown()
            case _:
                print("Skipping key press, wrong key pressed")


    else:
        print("Skipping key press, too long press time.")

    update(update_url, update_interval)
