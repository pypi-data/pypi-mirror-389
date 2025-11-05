import shutil
import time
from typing import Union
import requests
import subprocess
import platform
import inspect
import os
import psutil
import how.constants as const
import logging

logger = logging.getLogger(__name__)

def get_available_ollama_models() -> Union[list[str], dict]:
    """
    Fetches the list of available Ollama models from the local server.
    Returns a sorted list of model names on success, or a dict with failure info.
    """
    try:
        logger.debug("Fetching available Ollama models...")
        response = requests.get(f"{const.OLLAMA_HOST}/api/tags", timeout=5)

        if response.status_code == 200:
            models_data = response.json()
            return sorted(model['name'] for model in models_data.get('models', []))

        # handle non-200 responses
        try:
            error_detail = response.json().get('message', response.text)
        except ValueError:
            error_detail = response.text

        logger.error(f"Failed to get models: {error_detail}")
        return {
            'status': 'FAILED',
            'status_code': response.status_code,
            'message': error_detail
        }

    except requests.exceptions.RequestException as err:
        logger.warning("Ollama server not started. Attempting to start it...")
        try:
            check_ollama_is_running() 
        except Exception as start_err:
            logger.error(f"Failed to start Ollama: {start_err}")
        return {
            'status': 'FAILED',
            'status_code': 500,
            'message': str(err)
        }


def check_ollama_has_model(model_name: str) -> bool:
    """
    Returns True if the given model is available on Ollama, False otherwise.
    """
    models = get_available_ollama_models()
    if isinstance(models, list):
        return model_name in models
    return False


def check_ollama_is_running(timeout: int = 10, poll_interval: float = 0.5):
    """
    Check if Ollama is installed, and if not running, open it.
    Waits until the server responds or timeout is reached.
    """
    if not is_program_installed("ollama"):
        print(f"⚙️ {'Install:':>11} Ollama is not found.")
        return False

    if not is_program_running("ollama"):
        try:
            subprocess.run(["open", "--hide", "-a", "Ollama"], check=True)
            print(f"🚀 {'Starting:':>11} Ollama.")
        except subprocess.CalledProcessError:
            print(f"💥 {'Failed:':>11} Ollama failed to start")
            print(f"🔧 {'Setting:':>11} To Stop this check run: how2 --start-check False")
            return False

    # Wait for the server to become ready
    url = f"{const.OLLAMA_HOST}/api/version"  
    start_time = time.time()
    while True:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print(f"✅ {'Ready:':>11} Ollama server is ready.")
                return True
        except requests.exceptions.RequestException:
            pass  # server not ready yet

        if time.time() - start_time > timeout:
            print(f"💥 {'Timeout:':>11} Ollama server did not start within {timeout}s.")
            return False

        time.sleep(poll_interval)
        
def is_program_installed(program_name):
    """Check if the program exists on the path"""
    return shutil.which(program_name) is not None

def is_program_running(program_name):
    """Check if a program is running based on the program name."""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if program_name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logger.error(f"Error accessing process {proc.info['pid']}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while checking processes: {e}", exc_info=True)
        return False

