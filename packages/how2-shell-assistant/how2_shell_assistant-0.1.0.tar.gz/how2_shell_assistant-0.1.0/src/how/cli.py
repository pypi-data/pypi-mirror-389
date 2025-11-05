import argparse
import sys
from how.how_agent import agent
from how.utils.os_utils import copy_to_clipboard
from how.utils.config_utils import config


class FriendlyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        print(f"\n❌ ERROR: {message}\n", file=sys.stderr)
        print("💡 Example usage:", file=sys.stderr)
        print("   how2 <your question on a command line tool>\n", file=sys.stderr)
        sys.exit(2)


def main():
    parser = FriendlyArgumentParser(
        description="Ask how2 to do anything at the command line."
    )
    parser.add_argument(
        "--env",
        action="store_true",
        help="Print current environment setup",
    )
    parser.add_argument(
        "--history",
        nargs="?",
        const=True,  # means "--history" alone is valid
        help="Show command history or copy a specific entry (--history <num>)",
    )
    parser.add_argument(
        "--set-llm",
        metavar="MODEL",
        help="Set the Ollama model for how2",
    )
    parser.add_argument(
        "--set-temperature",
        metavar="TEMP",
        type=float,
        help="Set the LLM temperature for how2",
    )
    parser.add_argument(
        "--set-timeout",
        metavar="SECONDS",
        type=int,
        help="Set the LLM timeout for how2",
    )
    parser.add_argument(
        "--set-host",
        metavar="URL",
        help="Set the Ollama host for how2",
    )
    parser.add_argument(
        "question",
        nargs="*",
        help="Command-line question (e.g., 'how2 how do I zip a file?')",
    )

    args = parser.parse_args()

    # ----------------------------------------------------------
    # Handle environment info
    # ----------------------------------------------------------
    if args.env:
        env = config.as_dict()
        print("💻 Current Environment:")
        for k, v in env.items():
            print(f"  {k}: {v}")
        return

    # ----------------------------------------------------------
    # Handle --history [optional number]
    # ----------------------------------------------------------
    if args.history is not None:
        # user just typed --history
        if args.history is True:
            config.show_history()
            return

        # user typed --history <num>
        try:
            index = int(args.history)
        except ValueError:
            print("❌ Invalid history index. Please provide a number.")
            return

        command = config.get_history_command(index)
        if command:
            copy_to_clipboard(command)
            print(f"✅ Copied command #{index} to clipboard.")
            print(f"📋 {command}")
        else:
            print(f"⚠️ No command found for history index {index}.")
        return

    # ----------------------------------------------------------
    # Handle setting config values
    # ----------------------------------------------------------
    if args.set_llm:
        print(f"🤖 Setting LLM model to: {args.set_llm}")
        config.set("model_name", args.set_llm)
        return

    if args.set_temperature is not None:
        print(f"🌡️ Setting temperature to: {args.set_temperature}")
        config.set("temperature", args.set_temperature)
        return

    if args.set_timeout is not None:
        print(f"⏱️ Setting timeout to: {args.set_timeout}")
        config.set("timeout", args.set_timeout)
        return

    if args.set_host:
        print(f"🌐 Setting Ollama host to: {args.set_host}")
        config.set("ollama_host", args.set_host)
        return

    # ----------------------------------------------------------
    # Handle free-text questions
    # ----------------------------------------------------------
    if args.question:
        question_text = " ".join(args.question).strip()
        if question_text:
            command = agent.ask(question_text)
            if command:
                config.log_history(question=question_text, command=command)
                cmd_key = "⌘"  # ⌘ symbol
                print(f"Press {cmd_key} + V to paste the command")
                copy_to_clipboard(command)
            else:
                print("⚠️ No command generated.")
        else:
            print("Please enter a question or use --help for options.")


if __name__ == "__main__":
    main()
