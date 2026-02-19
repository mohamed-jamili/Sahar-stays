# =============================================================================
# Agent CLI: entry point called by api.php. Loads session, runs the agent,
# saves session, and prints the JSON response to stdout for PHP to capture.
# =============================================================================

import argparse
import json
import sqlite3
import sys
# Import the main agent class that talks to the LLM and runs tools
from agent import HotelConciergeAgent


def load_session(session_id):
    """Load conversation history and state for this session from SQLite."""
    # Open the database file (same one used for reservations)
    conn = sqlite3.connect("hotel_agent.db")
    cursor = conn.cursor()
    # context = serialized message list; state = e.g. IDLE or RUNNING
    cursor.execute("SELECT context, state FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        # Return parsed JSON context (list of messages) and state string
        return json.loads(row[0]), row[1]
    # No session yet: return empty dict and IDLE
    return {}, "IDLE"


def save_session(session_id, context, state):
    """Save conversation history and state for this session to SQLite."""
    conn = sqlite3.connect("hotel_agent.db")
    cursor = conn.cursor()
    # Upsert: insert or update by session_id (context is JSON string of messages)
    cursor.execute("""
    INSERT INTO sessions (session_id, context, state)
    VALUES (?, ?, ?)
    ON CONFLICT(session_id) DO UPDATE SET
        context=excluded.context,
        state=excluded.state
    """, (session_id, json.dumps(context), state))
    conn.commit()
    conn.close()


def main():
    # Parse command-line arguments (passed by api.php)
    parser = argparse.ArgumentParser()
    parser.add_argument("--session_id", required=True, help="Session ID for the user")
    parser.add_argument("--message", required=True, help="User message")
    args = parser.parse_args()

    # Load existing conversation for this session (or empty if new)
    context, state = load_session(args.session_id)

    # Context must be a list of messages for the LLM; if legacy dict, ignore it
    history = None
    if isinstance(context, list):
        history = context

    # Create the agent with optional conversation history (system + past messages + tool results)
    agent = HotelConciergeAgent(history=history)

    # Process the new user message: LLM may call tools, we get back { text, ui_action? }
    response = agent.process_input(args.message)

    # Persist updated conversation (agent.messages includes the new turn)
    save_session(args.session_id, agent.messages, "RUNNING")

    # Print JSON to stdout so PHP shell_exec can capture it and send to frontend
    print(json.dumps(response))


# When run as a script (python agent_cli.py ...)
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # On any error, still print valid JSON so the frontend gets a proper response
        print(json.dumps({"text": "Sorry, something went wrong. Please try again."}))
