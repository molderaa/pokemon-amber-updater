import os
import sys
import requests
import configparser
import shutil
import tempfile
import subprocess
from packaging import version
from pathlib import Path

# Define paths
UPDATER_FOLDER = os.path.dirname(os.path.abspath(__file__))
ROOT_FOLDER = os.path.abspath(os.path.join(UPDATER_FOLDER, "../../.."))  # Go up three directories to reach the "test" folder
# REMOTE_CONFIG_URL = ""

def get_config_path():
    # Check if the app is running as a frozen .exe (compiled with PyInstaller, cx_Freeze, etc.)
    if getattr(sys, 'frozen', False):
        # If running as a packaged .exe, get the path of the executable and adjust accordingly
        base_config_path = Path(sys.executable).parent
        config_path = base_config_path / 'config.ini'
    else:
        # If running as a script (not compiled), use the script's location
        base_config_path = Path(__file__).resolve().parents[2]  # Going up two directories
        config_path = base_config_path / 'config.ini'
    return config_path

CONFIG_FILE = get_config_path()

def get_local_version():
    # Use RawConfigParser to disable interpolation
    config = configparser.RawConfigParser()
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Local config file not found: {CONFIG_FILE}")
    config.read(CONFIG_FILE)
    return {
        "version": config["Version"]["current_version"],
        "url": config["Remote Config"]["url"]
    }

def get_remote_config(remote_config_url):
    response = requests.get(remote_config_url)
    if response.status_code == 200:
        # Use RawConfigParser to disable interpolation
        config = configparser.RawConfigParser()
        config.read_string(response.text)
        return {
            "version": config["Version"]["current_version"],
            "url": config["Download"]["url"]
        }
    else:
        raise Exception(f"Failed to fetch remote config: {response.status_code}")

# def download_to_temp(download_url):
#     temp_dir = tempfile.mkdtemp()
#     download_path = os.path.join(temp_dir, "new_version.zip")
#     response = requests.get(download_url, stream=True)
#     if response.status_code == 200:
#         with open(download_path, "wb") as file:
#             for chunk in response.iter_content(chunk_size=8192):
#                 file.write(chunk)
#         # print(f"Downloaded new version to {download_path}")
#         return temp_dir, download_path
#     else:
#         raise Exception(f"Failed to download new version: {response.status_code}")

def download_to_temp(download_url):
    temp_dir = tempfile.mkdtemp()
    download_path = os.path.join(temp_dir, "new_version.zip")
    response = requests.get(download_url, stream=True)

    if response.status_code == 200:
        total_size = int(response.headers.get('Content-Length', 0))  # Get total file size in bytes
        downloaded_size = 0

        with open(download_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)

                    # Calculate and display the download progress
                    percentage = (downloaded_size / total_size) * 100 if total_size else 0
                    print(f"\rDownloading: {percentage:.2f}%", end='')

        print("\nDownload complete.")  # Move to the next line after download
        return temp_dir, download_path
    else:
        raise Exception(f"Failed to download new version: {response.status_code}")

def replace_old_version(temp_dir, download_path):
    extract_dir = os.path.join(temp_dir, "extracted")
    shutil.unpack_archive(download_path, extract_dir)
    # print(f"Extracted new version to {extract_dir}")

    # Debugging output: print the ROOT_FOLDER to verify it's correct
    # print(f"ROOT_FOLDER: {ROOT_FOLDER}")
    
    # Ensure ROOT_FOLDER points to the right directory and handle deletion
    for item in os.listdir(ROOT_FOLDER):
        item_path = os.path.join(ROOT_FOLDER, item)
        # print(f"Checking item: {item_path}")  # Debugging output
        
        # Skip the 'Updater' directory from deletion
        if os.path.basename(item_path) == "Updater":
            # print(f"Skipping 'Updater' directory: {item_path}")
            continue

        if os.path.isdir(item_path):
            # print(f"Removing directory: {item_path}")  # Debugging output
            shutil.rmtree(item_path)
        else:
            # print(f"Removing file: {item_path}")  # Debugging output
            os.remove(item_path)
    # print("Old version deleted, excluding the updater folder.")

    print("Copying new files over")
    for item in os.listdir(extract_dir):
        # print(f"Movign {item}")
        shutil.move(os.path.join(extract_dir, item), ROOT_FOLDER)
        # print(f"Successfully moved {item} to {ROOT_FOLDER}")
    # print("New version installed.")

def main():
    try:
        local_version = get_local_version()
        # print(f"Local version: {local_version}")
        print(f"Local version: {local_version["version"]}")
        remote_config_url = local_version["url"]        

        remote_config = get_remote_config(remote_config_url)
        remote_version = remote_config["version"]
        download_url = remote_config["url"]
        print(f"Remote version: {remote_version}")
        # print(f"Download URL: {download_url}")

        if version.parse(remote_version) > version.parse(local_version["version"]):
            print("New version available. Downloading...")
            temp_dir, download_path = download_to_temp(download_url)
            try:
                replace_old_version(temp_dir, download_path)

                config = configparser.ConfigParser()
                config.read(CONFIG_FILE)
                config["Version"]["current_version"] = remote_version
                with open(CONFIG_FILE, "w") as configfile:
                    config.write(configfile)
                print("Update complete!")
            finally:
                shutil.rmtree(temp_dir)
                # print("Temporary files cleaned up.")
                try:
                    game_executable = os.path.join(ROOT_FOLDER, "Game.exe")  # Update "Game.exe" to your actual game executable name
                    print(game_executable)
                    subprocess.Popen([game_executable], cwd=ROOT_FOLDER)
                    print("Game relaunched successfully.")
                    sys.exit(0)  # Exit the updater process after successful relaunch
                except Exception as relaunch_error:
                    print(f"Failed to relaunch the game: {relaunch_error}")
        else:
            print("You are already using the latest version.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

input("Press Enter to exit...")
