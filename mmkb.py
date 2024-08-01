import argparse
import ctypes
import os.path
import time

import requests

VERSION = 3  # version of the script, has to be on top of the file
UPDATE_URL = "https://raw.githubusercontent.com/KilianSen/MiniKeyboard/master/mmkb.py"


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
                return

    with open("update.lock", "w") as f:
        f.write(str(int(time.time())))

    data = get_file_from_url(UPDATE_URL).split("\n")
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


if __name__ == "__main__":
    k, t = get_key_info()

    if t < 1:
        match k:
            case 1:
                mail()
            case 0:
                calc()
            case 2:
                lock()
    else:
        print("Skipping key press, too long press time.")

    update()
