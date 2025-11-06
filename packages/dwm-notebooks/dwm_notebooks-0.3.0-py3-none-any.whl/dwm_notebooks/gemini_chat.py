"""Terminal chat CLI for interacting with Google Gemini to write code."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - handled at runtime
    genai = None  # type: ignore


API_KEY = "AIzaSyDlP4SVcz-83mdsW4X-9J-ajY0aZY_yK78"
DEFAULT_MODEL = "gemini-2.5-flash"
SYSTEM_INSTRUCTION = "help me write code for the given instruction"
EXIT_COMMANDS = {"exit", "quit", "q"}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dwm-gemini",
        description="Chat with Google Gemini in the terminal to generate code snippets."
    )
    parser.add_argument(
        "--system-instruction",
        default=SYSTEM_INSTRUCTION,
        help="Override the system instruction priming Gemini (default: help me write code for the given instruction)."
    )
    return parser


def ensure_dependencies() -> None:
    if genai is None:
        print(
            "Error: The 'google-generativeai' package is required for dwm-gemini.\n"
            "Install it with 'pip install google-generativeai'.",
            file=sys.stderr,
        )
        sys.exit(1)


def fetch_api_key() -> str:
    return API_KEY


def build_chat(system_instruction: str, model_name: str = DEFAULT_MODEL):
    try:
        genai.configure(api_key=fetch_api_key())
        model = genai.GenerativeModel(model_name)
        chat = model.start_chat(history=[{"role": "user", "parts": [system_instruction]}])
        return chat
    except Exception as exc:  # pragma: no cover - runtime configuration issues
        print(f"Error: Failed to initialise Gemini client ({exc}).", file=sys.stderr)
        sys.exit(1)


def print_banner(system_instruction: str, model_name: str) -> None:
    print("=" * 60)
    print(" Google Gemini Terminal Chat")
    print(" Type your instruction and press Enter.")
    print(" Commands: 'exit', 'quit', or 'q' to leave.")
    print(f" System instruction: {system_instruction}")
    print(f" Gemini model: {model_name}")
    print("=" * 60)


def render_response(response) -> str:
    # response.text may be None if model returns structured data
    if hasattr(response, "text") and response.text:
        return response.text.strip()
    # Fallback to joining parts if available
    if hasattr(response, "candidates"):
        texts = []
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if getattr(part, "text", None):
                        texts.append(part.text)
        if texts:
            return "\n".join(texts)
    return "<No response text returned by model>"


def chat_loop(chat) -> None:
    while True:
        try:
            user_input = input("Input: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting dwm-gemini. Bye!")
            break

        if not user_input:
            continue
        if user_input.lower() in EXIT_COMMANDS:
            print("Exiting dwm-gemini. Bye!")
            break

        try:
            response = chat.send_message(user_input)
            content = render_response(response)
        except Exception as exc:  # pragma: no cover - API runtime issues
            print(f"Response: <Error contacting Gemini: {exc}>")
            continue

        print(f"Response: {content}")


def main(argv: Optional[list[str]] = None) -> None:
    ensure_dependencies()
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    print_banner(args.system_instruction, DEFAULT_MODEL)
    chat = build_chat(args.system_instruction, DEFAULT_MODEL)
    chat_loop(chat)


if __name__ == "__main__":  # pragma: no cover
    main()
