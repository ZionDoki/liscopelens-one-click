import os
import sys
import platform
import subprocess
import shutil
import tarfile
import zipfile
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from .logger import log_success, log_error, log_info
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn



def download_file(url, dest):
    log_info(f"Downloading {url}...")
    try:
        with urlopen(url) as response:
            total_size = int(response.info().get('Content-Length', 0))
            chunk_size = 1024  # Size of each chunk in bytes

            with open(dest, 'wb') as out_file, Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(f"Downloading {dest}", total=total_size)
                
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    progress.update(task, advance=len(chunk))
        
        log_info(f"Downloaded to {dest}")
    except HTTPError as e:
        log_error(f"HTTP Error: {e.code} - {e.reason}")
        sys.exit(1)
    except URLError as e:
        log_error(f"URL Error: {e.reason}")
        sys.exit(1)

def extract_file(file_path, extract_to):
    if file_path.endswith(".tar.gz"):
        log_info(f"Extracting {file_path}...")
        with tarfile.open(file_path, 'r:gz') as tar:
            tar.extractall(extract_to)
    elif file_path.endswith(".zip"):
        log_info(f"Extracting {file_path}...")
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    log_success(f"Extracted to {extract_to}")

def get_scancode():
    dir_path = "./scancode-toolkit"
    system_type = platform.system().lower()

    if system_type == "windows":
        os_type = "windows"
    elif system_type == "darwin":  # macOS is identified as 'Darwin'
        os_type = "macos"
    elif system_type == "linux":
        os_type = "linux"
    else:
        log_info("Unsupported operating system.")
        sys.exit(1)

    if os.path.exists(dir_path):
        log_info("Scancode toolchain already exists.")
        return
    
    python_version = f"{sys.version_info.major}.{sys.version_info.minor if sys.version_info.minor < 12 else 12}"
    log_info(f"Python version: {python_version}, downloading and installing scancode...")

    base_url = "https://github.com/nexB/scancode-toolkit/releases/download/v32.1.0/"
    file_extension = "tar.gz" if os_type in ["linux", "macos"] else "zip"
    file_name = f"scancode-toolkit-v32.1.0_py{python_version}-{os_type}.{file_extension}"
    download_url = base_url + file_name

    try:
        download_file(download_url, file_name)
        extract_file(file_name, ".")
        os.rename(f"scancode-toolkit-v32.1.0", dir_path)
        os.remove(file_name)
    except Exception as e:
        log_error(f"An error occurred: {e}")
        sys.exit(1)

    original_dir = os.getcwd()
    os.chdir(dir_path)
    log_info("Running scancode --help...")
    subprocess.run(["./scancode" if os_type in ["linux", "macos"] else "scancode.bat", "--help"])
    os.chdir(original_dir)