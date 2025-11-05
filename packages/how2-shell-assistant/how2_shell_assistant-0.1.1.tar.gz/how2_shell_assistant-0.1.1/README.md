# how2: Your Command-Line Shell Assistant

`how2` is a command-line tool that acts as your personal shell assistant. Powered by Large Language Models (LLMs), it translates your natural language questions into executable shell commands.

## Features

-   **Natural Language to Shell Commands**: Ask questions in plain English and get back the shell command you need.
-   **Command History**: `how2` keeps a history of your questions and the generated commands, so you can easily reuse them.
-   **Clipboard Integration**: The generated command is automatically copied to your clipboard, ready to be pasted into your terminal.
-   **Configurable LLM**: You can configure `how2` to use different LLM models from Ollama.
-   **Environment Aware**: `how2` provides context to the LLM about your operating system, current directory, and available tools to generate more accurate commands.

## High-Level Architecture

The `how2` assistant is composed of three main components:

1.  **Command-Line Interface (CLI)**: The `cli.py` module, built with Python's `argparse` library, provides the user interface. It handles user input, parses arguments, and calls the appropriate functions.

2.  **The Agent**: The `agent.py` module is the core of the application. It takes the user's question, constructs a detailed prompt with context about the user's environment, and sends it to the LLM using the `ollama` library. It then parses the LLM's response and extracts the shell command.

3.  **Utilities**:
    -   **`config_utils.py`**: This module provides a `ConfigManager` class that handles all aspects of configuration, including loading and saving settings, and managing the command history.
    -   **`os_utils.py`**: This module contains helper functions for interacting with the operating system, such as copying text to the clipboard and getting information about the environment.

## Installation

`how2` was written and tested on macOS *Windows dependencies are not addressed*
You can install `how2` using `pip`:

```bash
pip install .
```

This will install the `how2` command-line tool and its dependencies.

## Usage

To ask a question, simply use the `how2` command followed by your question:

```bash
how2 <your question>
```

For example:

```bash
how2 how do I zip a file?
```

The generated command will be printed to the console and copied to your clipboard.

### Other Commands

-   **Show History**: To see your command history, run:
    ```bash
    how2 --history
    ```
-   **Copy from History**: To copy a specific command from your history to the clipboard, use the command's index from the history view:
    ```bash
    how2 --history <command #>
    ```
-   **Set LLM Model**: To set the Ollama model you want to use, run:
    ```bash
    how2 --set-llm <model_name>
    ```
-   **Set LLM Temperature**: To set the LLM temperature, run:
    ```bash
    how2 --set-temperature <temperature_value>
    ```
-   **Set LLM Timeout**: To set the LLM timeout in seconds, run:
    ```bash
    how2 --set-timeout <timeout_in_seconds>
    ```
-   **Set Ollama Host**: To set the Ollama host URL, run:
    ```bash
    how2 --set-host <host_url>
    ```
-   **Show Environment**: To see the current environment setup that `how2` is using, run:
    ```bash
    how2 --env
    ```

## Configuration

`how2` stores its configuration in `~/.config/how2/settings.json`. You can manually edit this file to change the settings.

The default configuration is:

```json
{
    "model_name": "gpt-oss:20b-cloud",
    "ollama_host": "http://127.0.0.1:11434",
    "temperature": 0.3,
    "timeout": 50,
    "log_level": "INFO"
}
```

## Testing

The project uses `mlflow` to run tests and log the results. The test questions are defined in `src/tests/mlflow_test_how2.py`.

To run the tests, you will need to have `mlflow` installed (`pip install mlflow`). Then, you can run the test script:

```bash
python src/tests/mlflow_test_how2.py
```

You can then view the results using the `mlflow` UI:

```bash
mlflow ui
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on the project's GitHub repository.

## License

This project is licensed under the MIT License.
