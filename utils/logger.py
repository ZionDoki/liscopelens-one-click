import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("setup.log", mode="w"),
    ],
)

# ANSI escape codes for colors and styles
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"

def log_success(message, prefix=""):
    logging.log(25, prefix + f"{GREEN}{BOLD}[{'SUCCESS':>8}] {RESET}{GREEN}{message}{RESET}")

def log_error(message, prefix=""):
    logging.error(prefix + f"{RED}{BOLD}[{'ERROR':>8}] {RESET}{RED}{message}{RESET}")

def log_info(message, prefix=""):
    logging.info(prefix + f"{CYAN}{BOLD}[{'INFO':>8}] {RESET}{CYAN}{message}{RESET}")