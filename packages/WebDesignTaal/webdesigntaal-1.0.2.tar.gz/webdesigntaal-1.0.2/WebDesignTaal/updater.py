import os
import sys
import urllib.request
import zipfile
import shutil

# Path van de module zelf
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

GITHUB_VERSION_URL = "https://raw.githubusercontent.com/TJouleL/WebDesignTaal/main/version.txt"
LOCAL_VERSION_FILE = os.path.join(MODULE_DIR, "version.txt")
GITHUB_ZIP_URL = "https://github.com/TJouleL/WebDesignTaal/archive/refs/heads/main.zip"
UPDATE_DIR = os.path.join(MODULE_DIR, "update_temp")
ZIP_FILE = os.path.join(MODULE_DIR, "update.zip")

def get_local_version():
    if os.path.exists(LOCAL_VERSION_FILE):
        with open(LOCAL_VERSION_FILE, "r") as f:
            return f.read().strip()
    return "0.0.0"

def get_remote_version():
    try:
        with urllib.request.urlopen(GITHUB_VERSION_URL) as response:
            return response.read().decode().strip()
    except Exception as e:
        print(f"Kon remote version niet ophalen: {e}")
        return None

def needs_update():
    remote = get_remote_version()
    local = get_local_version()
    if remote is None:
        return False
    return local != remote

def download_and_extract():
    print("Downloaden van nieuwe versie...")
    urllib.request.urlretrieve(GITHUB_ZIP_URL, ZIP_FILE)
    with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
        zip_ref.extractall(UPDATE_DIR)

def apply_update():
    extracted_root = os.path.join(UPDATE_DIR, os.listdir(UPDATE_DIR)[0])
    for item in os.listdir(extracted_root):
        s = os.path.join(extracted_root, item)
        d = os.path.join(MODULE_DIR, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

def clean_up():
    if os.path.exists(UPDATE_DIR):
        shutil.rmtree(UPDATE_DIR)
    if os.path.exists(ZIP_FILE):
        os.remove(ZIP_FILE)

def update_from_github():
    download_and_extract()
    apply_update()
    clean_up()
    print("Update voltooid! Start het script opnieuw.")
    sys.exit(0)  # stop zodat volgende run met de nieuwe updater gebeurt

def auto_update():
    """Kan door andere scripts aangeroepen worden."""
    if needs_update():
        print(f"Nieuwe versie beschikbaar! ({get_local_version()} -> {get_remote_version()})")
        update_from_github()
    else:
        print(f"Script is up-to-date. Versie: {get_local_version()}")
