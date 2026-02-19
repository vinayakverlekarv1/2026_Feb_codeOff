"""Tri-tier console chatbot: KB, inventory DB, fallback. UK English, prices in GBP (£)."""
import sys

from router import chat

EXIT_COMMANDS = ("quit", "exit", "bye", "q")


def main() -> None:
    print("TechGear UK Chatbot. Type your question (or 'quit' to exit). All prices in GBP (£).\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not user_input:
            continue
        if user_input.lower() in EXIT_COMMANDS:
            print("Goodbye.")
            break
        response = chat(user_input)
        print(f"Bot: {response}\n")


if __name__ == "__main__":
    main()
    sys.exit(0)
