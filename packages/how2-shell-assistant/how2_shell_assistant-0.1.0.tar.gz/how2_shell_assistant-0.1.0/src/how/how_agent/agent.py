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


logger = logging.getLogger(__name__)
PROMPT = """SYSTEM:
You are an expert, concise shell assistant. Your goal is to provide accurate, executable shell commands.

CONTEXT:
-   **OS:** {current_os}
-   **Shell:** {shell}
-   **CWD:** {current_dir}
-   **User:** {current_user}
-   **Git Repo:** {git_repo}
-   **Files (top 20):** {files}
-   **Available Tools:** {tools}

RULES:
1.  **Primary Goal:** Generate the response JSON with the exact, executable shell command(s) for the `{shell}` environment.
   **Response Format Example:** {{ "type": "command", "content": "zip archive.zip file.txt" }}

2.  **Context is Key:** Use the CONTEXT (CWD, Files, OS, Tools) to write commands that are correct and specific.

3.  **No Banter:** Do NOT include greetings, sign-offs, or conversational filler.

4.  **Safety:** If a command is complex or destructive (e.g., `rm -rf`, `find -delete`), add a short comment explaining what it does.
   **Response Format Example:** {{ "type": "command", "content": "rm -rf temp/", "comment": "Deletes the temp directory and all its contents" }}

5.  **Questions:** If the user asks a general question (e.g., "what is `ls`?"), provide a concise, one-line answer.
   **Response Format Example:** {{ "type": "question", "content": "Lists files and directories in the current directory." }}

6.  **Ambiguity:** If the request is unclear, ask a single, direct clarifying question.
   **Response Format Example:** {{ "type": "question", "content": "Which file or directory would you like to zip?" }}

REQUEST:
{question}

RESPONSE:
"""

    
# -----------------------------
# Fill prompt function
# -----------------------------
def fill_prompt(question: str) -> str:
    return PROMPT.format(
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
        print("❌ Failed to parse response as JSON.")
        return None
    
    resp_type = data.get("type")
    content = data.get("content")
    comment = data.get("comment", None)

    if resp_type == "question":
        print(f"💡 Answer: {content}")
    elif resp_type == "command":
        cmd = content
        if comment:
            print(f"⚠️ Comment: {comment}")
        print(f"💻 Command: {cmd}")
    else:
        print(f"❌ Unknown response type: {resp_type}")
    return cmd


def ask(question_text:str):
    spinner = Spinner("Processing")
    spinner.start()
    response = generate_response(question_text)
    spinner.stop()
    command = parse_response(response)
    
    return command