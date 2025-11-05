import json
import os
import getpass
import platform
import subprocess
import traceback
from typing import Optional
import ollama
from pathlib import Path
from how.utils.os_utils import get_git_repo, list_available_tools, Spinner, list_files
from how.utils.config_utils import config
import logging
import how.constants as const

logger = logging.getLogger(__name__)

    
# -----------------------------
# Fill prompt function
# -----------------------------
def fill_prompt(question: str) -> str:
    return const.PROMPT.format(
        current_os=f"{platform.system()} {platform.release()}",
        shell=os.environ.get("SHELL", "unknown"),
        current_dir=os.getcwd(),
        current_user=getpass.getuser(),
        git_repo=get_git_repo(),
        files=list_files(),
        tools=list_available_tools(),
        question=question
    )

def generate_response(
        question: str,
        model_name: str = config.get("model_name"),
        ollama_host: Optional[str] = config.get("ollama_host"),
        timeout: int = config.get("timeout"),
        temperature: float = config.get("temperature")
    ) -> Optional[str]:
    content = None

    if ollama_host:
        os.environ["OLLAMA_HOST"] = ollama_host.rstrip("/")

    try:
        prompt = fill_prompt(question)
        client = ollama.Client(timeout=timeout)
        response = client.generate(
            model=model_name, prompt=prompt, options={"temperature": temperature}
        )

        if response.get("response") is not None:
            #print(json.dumps(response, indent=2))
            #print(response)
            content = response["response"].strip()
        else:
            print("THIS IS A PROBLEM: No Response generated.")
        
    except Exception as e:
        traceback.print_exc() 
        logging.error(f"Ollama call failed or timed out: {e}")

    return content

def parse_response(response):

    cmd = None
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        print(f"❌ {'Response:':>11} Failed to parse response as JSON.")
        return None
    
    resp_type = data.get("type")
    content = data.get("content")
    comment = data.get("comment", None)

    if resp_type == "question":
        print(f"💡 {'Answer:':>11} {content}")
    elif resp_type == "command":
        cmd = content
        if comment:
            print(f"💬 {'Comment:':>11} {comment}")
        print(f"💻 {'Command:':>11} {cmd}")
    else:
        print(f"❌ {'Response:':>1} Unknown response type: {resp_type}")
    return cmd


def ask(question_text:str):
    spinner = Spinner("Processing")
    spinner.start()
    response = generate_response(question_text)
    spinner.stop()
    command = parse_response(response)
    
    return command