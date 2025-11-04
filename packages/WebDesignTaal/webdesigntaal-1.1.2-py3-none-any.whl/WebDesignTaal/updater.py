"""updater.py

De updater.py is voor manuele updates doen via github.


"""

import sys
import urllib.request
import subprocess
import socket
from importlib.metadata import version, PackageNotFoundError

GITHUB_VERSION_URL = "https://raw.githubusercontent.com/TJouleL/WebDesignTaal/refs/heads/main/WebDesignTaal/version.txt"


def is_online(host="google.com", port=443, timeout=3):
    "Check of het huidige device internet connectie heeft"
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except OSError:
        return False


def get_local_version(silent=False):
    "Check local version and return its contents."
    try:
        return version("WebDesignTaal")
    except PackageNotFoundError:
        if not silent:
            print("WebDesignTaal package kon niet gevonden worden. Is hij wel geïnstalleerd?")
        return "0.0.0"
    except Exception as e:
        if not silent:
            print(f"Kon lokale version niet ophalen: {e}")
        return "0.0.0"

def get_remote_version(silent=False):
    "Open remote version file and return its contents."
    try:
        with urllib.request.urlopen(GITHUB_VERSION_URL) as response:
            return str(response.read().decode().strip())
    except Exception as e:
        if not silent:
            print(f"Kon remote version niet ophalen: {e}")
        return None

def needs_update():
    "Check if the local version is different from the remote version."
    remote = tuple(map(int, get_remote_version().split(".")))
    local = tuple(map(int, get_local_version().split(".")))

    if remote > local:
        return True
    return False

def upgrade_package():
    "Safely upgrades the WebDesignTaal package"

    # Both are done to prevent broken updates when WebDesignTaal is uninstalled via pip
    cmd1 = [sys.executable, "-m", "pip", "install", "WebDesignTaal"]
    cmd2 = [sys.executable, "-m", "pip", "install", "--upgrade", "WebDesignTaal"]
    try:
        subprocess.check_call(cmd1)
        subprocess.check_call(cmd2)
        print("Upgrade succesvol!")
    except subprocess.CalledProcessError:
        print("Upgrade failed.")

def auto_update():
    """Can be caled by other scripts to check for updates and update if needed."""
    if is_online():
        if needs_update():
            print(f"Nieuwe versie beschikbaar! ({get_local_version(silent=True)} -> {get_remote_version(silent=True)})")
            antwoord = input("Wil je updaten? (Y/n) : ")
            if antwoord.lower() == "y" or antwoord.lower() == "":
                upgrade_package()
            else:
                pass