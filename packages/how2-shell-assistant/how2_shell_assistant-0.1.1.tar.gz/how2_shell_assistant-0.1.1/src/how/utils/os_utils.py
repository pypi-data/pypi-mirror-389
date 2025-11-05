import itertools
from pathlib import Path
import platform
import shutil
import subprocess
import threading
import psutil
import sys
import time
import pyperclip
import logging
import os

logger = logging.getLogger(__name__)

def copy_to_clipboard(text: str):
    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException as e:
        logger.warning(f"Clipboard copy failed: {e}")

def mac_notify(title, message, sound="Ping"):
    if platform.system() != "Darwin":
        logger.warning("⚠️ mac_notify: This feature is only supported on macOS.")
        return None

    os.system(f'''
        osascript -e 'display notification "{message}" with title "{title}" sound name "{sound}"'
    ''')

    
def list_available_tools() -> str:
    tools = [t for t in ["git","curl", "wget", "awk","sed","python", "pip", "brew", "zip", "unzip","npm","node","docker","java","mvn","gradle"] if shutil.which(t)]
    return ", ".join(tools)


def get_git_repo():
    try:
        repo_path = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return os.path.basename(repo_path)
    except subprocess.CalledProcessError:
        return "None"

def list_files(limit=10):
    cwd = Path.cwd()
    entries = [p.name for p in cwd.iterdir()]
    return ", ".join(entries[:limit])

class Spinner:
    def __init__(self, message="Generating"):
        self.message = message
        self._stop_event = threading.Event()
        self._spinner_thread = None

    def _spinner(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        for frame in itertools.cycle(frames):
            if self._stop_event.is_set():
                break
            sys.stdout.write(f"\r{frame} {self.message}")
            sys.stdout.flush()
            time.sleep(0.1)
        # Clear the line after stopping
        sys.stdout.write("\r" + " " * (len(self.message) + 2) + "\r")
        sys.stdout.flush()

    def start(self):
        """Start the spinner in a background thread."""
        self._stop_event.clear()
        if self._spinner_thread is None or not self._spinner_thread.is_alive():
            self._spinner_thread = threading.Thread(
                target=self._spinner,
                daemon=True
            )
            self._spinner_thread.start()

    def stop(self):
        """Stop the spinner and wait for the thread to finish."""
        self._stop_event.set()
        if self._spinner_thread is not None:
            self._spinner_thread.join()
            self._spinner_thread = None
            
        