#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path

from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown


def get_config_dir() -> Path:
    """Return the configuration directory for tux-gpt based on OS."""
    if os.name == "nt":
        base = Path(
            os.getenv(
                "APPDATA",
                Path.home() / "AppData" / "Roaming"
            )
        )
    else:
        base = Path(
            os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")
        )
    return base / "tux-gpt"


CONFIG_DIR: Path = get_config_dir()
CONFIG_PATH: Path = CONFIG_DIR / "config.json"
HISTORY_PATH: Path = CONFIG_DIR / "history.json"
INPUT_HISTORY_PATH: Path = CONFIG_DIR / "input_history"
MAX_HISTORY: int = 20


def write_default_config() -> None:
    """Create default configuration file with default model."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    default_config: dict[str, str] = {"model": "gpt-4.1-mini"}
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(default_config, f, indent=2)


def load_config() -> dict[str, object]:
    """Load CLI configuration, writing default if missing."""
    if not CONFIG_PATH.exists():
        write_default_config()
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: failed to load config {CONFIG_PATH}: {e}")
        return {"model": "gpt-4.1-mini"}


def load_history() -> list[dict[str, str]]:
    """Load persisted conversation history (up to MAX_HISTORY)."""
    if not HISTORY_PATH.exists():
        return []
    try:
        with HISTORY_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: failed to load history {HISTORY_PATH}: {e}")
        return []


def save_history(history: list[dict[str, str]]) -> None:
    """Persist conversation history, keeping only last MAX_HISTORY messages."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with HISTORY_PATH.open("w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Warning: failed to save history {HISTORY_PATH}: {e}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Interactive GPT-powered assistant for the terminal."
    )
    parser.add_argument(
        "-q",
        "--query",
        help="Send a single prompt and output the response."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Force the response to be returned as JSON."
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for tux-gpt CLI."""
    args = parse_args()
    console = Console()

    # ensure config directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        console.print(
            "[red]Please set your OPENAI_API_KEY environment variable.[/red]"
        )
        sys.exit(1)

    config = load_config()
    model = config.get("model", "gpt-5-mini")
    supported_models = ("gpt-5-mini", "gpt-4.1", "gpt-4.1-mini")
    if model not in supported_models:
        console.print(
            f"[red]Model '{model}' not supported. Choose one of: "
            f"{', '.join(supported_models)}[/red]"
        )
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    system_content = (
        "You are Tux-GPT, a virtual assistant that can search the web. Always "
        "search the web when user asks for something data related. "
        "For example: 'What is the weather today?' or 'Which date is "
        "today?'. You are running in a Linux terminal. Return responses "
        "formatted in Markdown so they can be rendered in the terminal "
        "using rich."
    )
    expect_json = args.json
    if args.json:
        system_content += (
            " When responding, return only a JSON object with an 'answer' "
            "field (string) summarizing the result and a 'sources' field "
            "(array of strings) listing any references used."
        )

    system_msg: dict[str, str] = {
        "role": "system",
        "content": system_content,
    }

    persisted = load_history()

    def process_user_input(user_input: str) -> None:
        call_history: list[dict[str, str]] = (
            [system_msg]
            + persisted
            + [{"role": "user", "content": user_input}]
        )

        try:
            with console.status("[bold green]", spinner="dots"):
                resp = client.responses.create(
                    model=model,
                    input=call_history,  # type: ignore[arg-type]
                    tools=[{"type": "web_search_preview"}],
                )
        except Exception as exc:
            console.print(f"[red]Error calling OpenAI API: {exc}[/red]")
            return

        answer = resp.output_text.strip()

        if expect_json:
            try:
                parsed = json.loads(answer)
                serialized = json.dumps(parsed, ensure_ascii=False, indent=2)
                console.print(serialized)
            except json.JSONDecodeError:
                console.print(
                    "[red]Warning: response was not valid JSON. "
                    "Raw output follows.[/red]"
                )
                console.print(answer)
        else:
            console.print()
            console.print(Markdown(answer))
            console.print()

        persisted.append({"role": "user", "content": user_input})
        persisted.append({"role": "assistant", "content": answer})

        if len(persisted) > MAX_HISTORY:
            del persisted[:-MAX_HISTORY]

        save_history(persisted)

    if args.query:
        process_user_input(args.query)
        return

    # setup multi-line input session with Ctrl+Enter to submit
    session = None
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.history import FileHistory

        kb = KeyBindings()

        # Enter should insert a newline (multi-line support)
        @kb.add('enter')
        def _(event):  # pylint: disable=redefined-outer-name
            event.current_buffer.insert_text('\n')

        # Use Ctrl+J to submit the message (as terminals typically cannot distinguish Ctrl+Enter)
        @kb.add('c-j')
        def _(event):  # pylint: disable=redefined-outer-name
            event.app.current_buffer.validate_and_handle()

        session = PromptSession(
            multiline=True,
            key_bindings=kb,
            history=FileHistory(str(INPUT_HISTORY_PATH)),
        )
    except ImportError:
        console.print(
            "[red]Warning: prompt_toolkit not installed. "
            "Falling back to single-line input. "
            "Install prompt-toolkit for multi-line input.[/red]"
        )

    welcome_message = (
        "\n             Welcome to the tux-gpt!\n"
        " This is a terminal-based interactive tool using GPT.\n"
        "  Please visit https://github.com/fberbert/tux-gpt\n"
        " Type Ctrl+J to submit your input. Type 'exit' to quit.\n"
    )
    console.print(f"[bold blue]{welcome_message}[/bold blue]", justify="left")

    while True:
        try:
            if session:
                user_input = session.prompt("> ")
            else:
                user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            console.print("\nExiting.")
            break

        if not user_input.strip():
            continue

        if user_input.strip().lower() in ("exit", "quit"):
            console.print("Exiting.")
            break

        process_user_input(user_input)


if __name__ == "__main__":
    main()
