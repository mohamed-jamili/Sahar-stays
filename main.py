# =============================================================================
# Simple CLI loop for testing the agent in the terminal (no web server).
# User types messages; agent responds with text (dict with "text" key).
# =============================================================================

from agent import HotelConciergeAgent
from dotenv import load_dotenv
import os


def main():
    # Load environment variables (API key, etc.)
    load_dotenv()
    # Create agent with no history (fresh conversation)
    agent = HotelConciergeAgent()

    # Print welcome message
    print("------------------------------------------------------------")
    print("Hello, I'm your AI hotel concierge. Where would you like to stay and for which dates?")
    print("(Type 'quit' to exit)")
    print("------------------------------------------------------------")

    # Main loop: read user input, call agent, print response
    while True:
        user_text = input("\nUser: ")
        if user_text.lower() in ["quit", "exit"]:
            break

        # process_input returns a dict (e.g. {"text": "...", "ui_action": {...}})
        response = agent.process_input(user_text)
        print(f"\nConcierge: {response}")


if __name__ == "__main__":
    main()
