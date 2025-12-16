import os
import sys
import time
import json
import uuid
import venv
import queue
import getpass
import argparse
import platform
import subprocess
import threading
import itertools
from pathlib import Path
from utils.preinstall import get_scancode
from utils.logger import log_success, log_error, log_info, YELLOW, RESET, CYAN

password = None
VENV_DIR = "venv"  # Name or path to the virtual environment
LICT_CMD = "liscopelens"
SYSTEM_SPC = {
    "standard": "docker_oh_standard",
    "small": "docker_oh_small",
    "minimal": "docker_oh_mini",
    "hpm": "openharmony-docker",
}
DOCKER_TAG = "3.2"  # Default tag for the Docker image
DOCKER_URL = "swr.cn-south-1.myhuaweicloud.com/openharmony-docker/"

def convert_line_endings_to_unix(path):
    """
    Convert line endings in files to Unix format (LF).
    
    If run on windows platform, the CRLF line will lead to error when 
    run build/prebuilts_download.sh in docker. So we need to convert it to LF.
    This function will recursively walk through the directory and convert all files.
    """
    for root, _, files in os.walk(path):
        # pass .repo and .git directories
        if ".repo" in root or ".git" in root:
            continue
        for name in files:
            file_path = os.path.join(root, name)
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                new_content = content.replace(b'\r\n', b'\n')
                with open(file_path, 'wb') as f:
                    f.write(new_content)
            except Exception as e:
                log_info(f"Skipping {file_path}: {e}")


def fetch_openharmony_source(oh_path: Path, branch: str, docker_image: str):
    """Run *repo init/sync/lfs* **inside** docker so host machine stays clean.
    
    Args:
        oh_path: Path to store OpenHarmony source code
        branch: Branch name (e.g., "master", "OpenHarmony-4.0-Release")
        docker_image: Docker image to use for the build environment
    """
    if (oh_path / ".repo").exists():
        log_success("Existing source tree detected – skip download.")
        return

    oh_path.mkdir(parents=True, exist_ok=True)
    
    # Check if branch exists before fetching
    log_info(f"Checking if branch exists: {branch}")
    if not check_branch_exists("https://gitee.com/openharmony/manifest", branch):
        raise ValueError(f"Branch '{branch}' does not exist in OpenHarmony manifest repository")

    # Shell snippet executed inside the container.
    script = f"""
        set -e
        cd /home/openharmony
        # Ensure repo tool is present
        if ! command -v repo >/dev/null 2>&1; then
            echo 'repo not found inside container – downloading…'
            wget -O ./repo https://gitee.com/oschina/repo/raw/fork_flow/repo-py3
            chmod +x ./repo
        fi
        ./repo init -u https://gitee.com/openharmony/manifest -b {branch} --no-repo-verify
        ./repo sync -c --no-tags --optimized-fetch
        ./repo forall -c 'git lfs pull'
    """

    log_info(f"Cloning OpenHarmony sources (branch: {branch}) inside Docker – this may take a while...")

    # Use the custom function for better output and process handling
    run_command_with_timeout(
        [
            "sudo",
            "docker",
            "run",
            "--rm",
            "-v",
            f"{oh_path}:/home/openharmony",
            docker_image,
            "bash",
            "-c",
            script,
        ],
        description="Cloning OpenHarmony sources",
        live_output=True  # Show output in real-time
    )

    log_success("Source checkout completed.")
    

def check_branch_exists(repo_url: str, branch: str) -> bool:
    """Check if a branch exists in the remote repository using git ls-remote."""
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "--exit-code", repo_url, branch],
            capture_output=True,
            text=True,
            check=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False

def run_command_with_timeout(command: list[str], description="", timeout=None, live_output=False, abort_condition_callback=None, abort_check_interval=10):
    """
    Run a command with a timeout, capture its output, and handle exceptions in a separate thread.
    Optionally display output in real-time.
    If the command contains 'sudo', prompt for the password and provide it securely.

    Parameters:
    - command: List[str] - The command and its arguments to execute.
    - description: str - A description to display alongside the loading spinner.
    - timeout: float or None - Maximum time in seconds to allow the command to run. If None, no timeout is applied.
    - live_output: bool - If True, display the command output in real-time.
    - abort_condition_callback: callable or None - A callback function that returns True if the process should be aborted.
    - abort_check_interval: int - Interval (in seconds) between abort condition checks.

    Returns:
    - str: The captured output from the command.

    Raises:
    - Exception: Any exception raised during the execution of the command.
    - subprocess.TimeoutExpired: If the command exceeds the specified timeout.
    """
    global password
    output = []  # To capture command output
    exception_queue = queue.Queue()  # Queue to capture exceptions

    # Check if the command includes 'sudo'
    if "sudo" in command:
        if platform.system().lower() == "linux" or platform.system().lower() == "darwin":
            use_sudo = True
            # Prompt the user securely for the sudo password
            if not password:
                password = getpass.getpass("Enter sudo password: ")
            # Modify the command to include '-S' to read the password from stdin
            sudo_index = command.index("sudo")
            command.insert(sudo_index + 1, "-S")
        else:
            # Remove 'sudo' from the command
            command = [cmd for cmd in command if cmd != "sudo"]
            log_info("Removed 'sudo' from the command as the OS is not Linux.")

    # We'll store the process reference in an external variable to allow the abort thread to kill it
    process_ref = {"proc": None, "finished": False}

    def target():
        try:
            # Start the subprocess with pipes for stdin and stdout
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",  # 或 "gbk"
                errors="replace",  # 替换无法解码的字符
                text=True,
                bufsize=1,  # Line-buffered
                universal_newlines=True,
            )
            process_ref["proc"] = process

            if live_output:
                # Read line by line and print in real-time
                with open(os.devnull, "w") as devnull:
                    for line in iter(process.stdout.readline, ""):
                        print(line, end="")  # Print to console
                        output.append(line)
                process.stdout.close()
                process.wait()
            else:
                try:
                    if password:
                        # Send the password followed by a newline
                        stdout, _ = process.communicate(password + "\n", timeout=timeout)
                    else:
                        stdout, _ = process.communicate(timeout=timeout)
                    output.append(stdout)
                except subprocess.TimeoutExpired:
                    log_error(f"Command timed out after {timeout} seconds.")
                    process.kill()
                    stdout, _ = process.communicate()
                    exception_queue.put(subprocess.TimeoutExpired(process.args, timeout))
                    return

        except Exception as e:
            exception_queue.put(e)
        finally:
            process_ref["finished"] = True

    # Start the thread to run the command
    thread = threading.Thread(target=target)
    thread.start()

    def abort_monitor():
        # This thread periodically checks if we need to abort
        while not process_ref["finished"]:
            time.sleep(abort_check_interval)
            if abort_condition_callback and abort_condition_callback():
                proc = process_ref["proc"]
                if proc and proc.poll() is None:
                    # Abort the process
                    log_info("Abort condition met. Terminating the command...")
                    proc.terminate()
                break

    if abort_condition_callback:
        monitor_thread = threading.Thread(target=abort_monitor, daemon=True)
        monitor_thread.start()

    # Loading effect
    spinner = itertools.cycle(["|", "/", "-", "\\"])
    while thread.is_alive():
        sys.stdout.write(f"\r{description} ... {next(spinner)} ")
        sys.stdout.flush()
        time.sleep(0.1)

    sys.stdout.write("\r" + " " * 80 + "\r")  # Clear the loading effect

    # Ensure the thread finishes
    thread.join()

    # Check for exceptions in the thread
    if not exception_queue.empty():
        exception = exception_queue.get()
        raise exception

    output = [o for o in output if o is None ]  # Remove None lines
    return "".join(output) if output else ""


def create_venv(venv_dir):
    """Create a virtual environment."""
    log_info("Setting up virtual environment...")
    if not os.path.exists(venv_dir):
        log_info(f"Creating virtual environment at: {venv_dir}...")
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        log_success(f"Virtual environment created at {venv_dir}.")


def check_and_install_cmd(venv_dir, cmd):
    """Check if a command is installed in the virtual environment and install it if missing."""
    venv_bin = Path(venv_dir) / "bin" if os.name != "nt" else Path(venv_dir) / "Scripts"
    pip_executable = venv_bin / "pip"

    try:
        # Check if the command exists
        run_command_with_timeout([venv_bin / cmd, "--help"], description=f"Checking '{cmd}' installation")
        log_success(f"'{cmd}' is already installed.")
    except FileNotFoundError:
        # Command not found, install via pip
        log_info(f"'{cmd}' not found. Installing liscopelens via pip...")
        subprocess.check_call([str(pip_executable), "install", "liscopelens"])
        log_success(f"'{cmd}' installed successfully.")


def check_and_pull_docker(image_name):
    """Check if a Docker image exists and pull it if missing."""
    try:
        log_info(f"'{image_name}' image not found. Pulling the latest version...")
        run_command_with_timeout(
            ["sudo", "docker", "pull", image_name],
            description=f"Pulling '{image_name}' image",
        )
        log_success(f"'{image_name}' image pulled successfully.")
    except Exception as e:
        log_success(f"'{image_name}' image pulled failed.")
        sys.exit(1)


def run_in_venv(venv_dir, command):
    """Run a command inside the virtual environment."""
    venv_bin = Path(venv_dir) / "bin" if os.name != "nt" else Path(venv_dir) / "Scripts"
    log_info(f"Running command in virtual environment: {command}")
    result = subprocess.run([venv_bin / command[0]] + command[1:], check=True)
    log_success(f"Command '{' '.join(map(str, command))}' executed successfully.")
    return result


def check_out_json(oh_path, product_name, docker_image, args) -> str:
    """Check if out.json exists and provide manual instructions if it doesn't."""
    out_json_path = Path(oh_path) / "out" / product_name / "out.json"
    if os.path.exists(out_json_path):
        log_success(f"Build successful. Found 'out.json' at: {out_json_path}")
    else:
        log_error(f"'out.json' not found at: {out_json_path}")
        log_error("Build may have failed. Please execute the following steps inside the Docker container manually:")
        manual_commands = [
            (
                f" 1. sudo docker run --rm -v {os.path.abspath(args.oh_path)}:/home/openharmony {docker_image}\n"
                f' 2. ./build/prebuilts_download.sh && ./build.sh --product-name {args.product_name} --gn-flags="--ide=json" '
                f'--gn-flags="--json-file-name=out.json" --no-prebuild-sdk\n'
                f"{RESET}After build success, run: {CYAN}exit\n"
                f" 3. source {os.path.join('venv', 'bin', 'activate')}"
                if os.name != "nt"
                else f"{os.path.join('venv', 'Scripts', 'activate')}"
            ),
            f" 4. python utils/scan.py {oh_path}\n" f" 5. {LICT_CMD} {oh_path}",
        ]
        for cmd in manual_commands:
            print(f"{CYAN}{cmd}{RESET}")
        log_error("Ensure that Docker is running and you have the necessary permissions.")
        log_error("BTW, if you encounter any problem, feel free to submit issue.")
        sys.exit(1)
    return out_json_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OpenHarmony licence audit pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    parser.add_argument("--download", action="store_true", help="Checkout/update sources inside Docker before build")
    parser.add_argument("--system_spec", default="standard", help="Docker system spec key or direct image name")
    parser.add_argument("--tag", default=DOCKER_TAG, help="Docker image tag")
    parser.add_argument("--oh_path", default="./oh-source", help="Path to OpenHarmony sources on host")
    parser.add_argument("--product_name", default="rk3568", help="Product name to build inside Docker")
    parser.add_argument("--output", default="./output", help="Output directory for licence report")
    parser.add_argument("--shadow", help="Node2license JSON file for shadow mode")

    parser.add_argument("--branch", 
                   help="OpenHarmony release tag branch (required if --download is set)")

    args = parser.parse_args()

    # 手动验证参数依赖关系
    if args.download and not args.branch:
        parser.error("--branch is required when --download is specified")

    docker_name = f"oh-{uuid.uuid4()}"
    docker_system_spec = SYSTEM_SPC.get(args.system_spec, args.system_spec)
    docker_image = f"{DOCKER_URL}{docker_system_spec}:{args.tag}"

    if args.download:
        check_and_pull_docker(docker_image)  # Need image for repo as well
        fetch_openharmony_source(Path(args.oh_path).resolve(), args.branch, docker_image)
    else:
        if not Path(args.oh_path).exists():
            log_error("Source path is missing – use --download to fetch automatically.")
            sys.exit(1)

    create_venv(VENV_DIR)
    get_scancode()
    check_and_install_cmd(VENV_DIR, LICT_CMD)

    check_and_pull_docker(docker_image)

    if os.path.exists(args.oh_path):
        log_info(f"OpenHarmony source code path exists: {args.oh_path}")
    else:
        log_error(f"OpenHarmony source code path not found: {args.oh_path}")
        log_error("Please provide the correct path to the OpenHarmony source code.")
        sys.exit(1)

    log_info("------ Build OH in Docker ------", prefix="\n")

    
    def abort_if_out_json_exists():
        out_json_path = Path(args.oh_path) / "out" / args.product_name / "out.json"
        if not out_json_path.exists():
            return False
        
        try:
            with open(out_json_path, 'r', encoding="utf-8") as f:
                content1 = json.load(f)
            
            time.sleep(1)
            with open(out_json_path, 'r', encoding="utf-8") as f:
                content2 = json.load(f)
                
            if content1 == content2:
                return True
            return False
            
        except (json.JSONDecodeError, IOError) as e:
            log_info(f"File not ready yet: {e}")
            return False
    
    run_command_with_timeout(
        [
            "sudo",
            "docker",
            "run",
            "--rm",
            "--name",
            docker_name,
            "-v",
            f"{os.path.abspath(args.oh_path)}:/home/openharmony",
            docker_image,
            "sh",
            "-c",
            f'./build/prebuilts_download.sh && ./build.sh --product-name {args.product_name} '
            f'--gn-flags="--ide=json" --gn-flags="--json-file-name=out.json"'
        ],
        description=f"This may take a long time, you can check log from {os.path.join(args.oh_path,'build.log')}",
        abort_condition_callback=abort_if_out_json_exists,
        abort_check_interval=20  # 每隔10秒检查一次
    )

    gn_json_path = check_out_json(args.oh_path, args.product_name, docker_image, args)
    run_command_with_timeout(["sudo", "docker", "kill", docker_name])

    log_info("------ Running Scancode ------", prefix="\n")
    log_info(args.oh_path + os.path.sep)
    run_in_venv(VENV_DIR, ["python", os.path.normpath("./utils/scan.py"), args.oh_path + os.path.sep])

    log_info("------ Running liscopelens ------", prefix="\n")
    scancode_result_dir = args.oh_path.split(os.path.sep)[-1] + "-license"
    log_info(scancode_result_dir)
    run_in_venv(
        VENV_DIR,
        [
            LICT_CMD,
            "cpp",
            "--gn_file",
            gn_json_path,
            "--scancode-dir",
            scancode_result_dir,
            "--ignore-unk",
            *(["--shadow-license", args.shadow] if args.shadow and os.path.exists(args.shadow) else []),
            "--output",
            args.output
        ],
    )
