# Chatbot Integration — Agentic AI Hotel Concierge

**School Project: Agentic AI**

This document explains how the AI chatbot was integrated into the Sahar Stays hotel booking website.

---

## 1. Overview

The chatbot is an **agentic AI** system: it uses an LLM (Large Language Model) that can call **tools** (functions) to perform actions such as searching hotels, booking rooms, and recommending activities. Instead of only answering with text, it interacts with the application’s data and logic.

---

## 2. Architecture

The integration is built in three layers:

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (index.html)                                           │
│  • React chat widget (floating panel)                            │
│  • Sends messages to API, displays replies                       │
│  • Updates hotel cards/city filter based on ui_action            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ POST /api.php { session_id, message }
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND API (api.php)                                           │
│  • Receives JSON with session_id and message                     │
│  • Calls Python agent via shell_exec                             │
│  • Returns JSON: { text, ui_action? }                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ python agent_cli.py --session_id ... --message "..."
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT (Python)                                                  │
│  • agent_cli.py: Entry point, session load/save                  │
│  • agent.py: HotelConciergeAgent, LLM + tools                    │
│  • tools.py: search_hotels, book_room, etc.                      │
│  • system_prompt.md: Instructions for the LLM                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Request Flow

1. **User types a message** in the chat widget.
2. **Frontend** sends a POST request to `api.php` with:
   - `session_id` (e.g. `sess_abc123`)
   - `message` (user text)
3. **api.php** runs:
   ```bash
   python agent_cli.py --session_id "sess_abc123" --message "Show me hotels in Paris"
   ```
4. **agent_cli.py**:
   - Loads conversation history from SQLite for this session
   - Creates `HotelConciergeAgent` with that history
   - Calls `agent.process_input(message)`
   - Saves the updated conversation
   - Prints JSON to stdout
5. **agent.py** (`process_input`):
   - Appends user message to `messages`
   - Calls the LLM with tools (search_hotels, book_room, etc.)
   - If the LLM calls a tool, executes it and feeds the result back
   - Gets a final text response
   - Returns `{ "text": "...", "ui_action": { ... } }`
6. **api.php** captures the JSON output and sends it back to the frontend.
7. **Frontend**:
   - Appends the bot reply to the chat
   - If `ui_action.filter_city` is present, filters hotel cards by city
   - If `ui_action.show_hotel_details` is present, opens the hotel detail view

---

## 4. Main Components

### 4.1 Frontend (index.html)

- **ChatWidget**: Floating chat panel with:
  - Message list (user vs bot)
  - Input field + send button
  - Loading indicator

- **API call**:

  ```javascript
  fetch("api.php", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, message: userMsg }),
  });
  ```

- **Session ID**: Generated once per page load:

  ```javascript
  const [sessionId] = React.useState(
    "sess_" + Math.random().toString(36).substr(2, 9),
  );
  ```

- **UI actions**: When the response includes `ui_action`, the app updates:
  - City filter → `filter_city`
  - Hotel detail view → `show_hotel_details`

### 4.2 Backend API (api.php)

- Reads `session_id` and `message` from the POST body
- Runs the Python agent with those arguments
- Sends back the agent’s JSON (`text` + optional `ui_action`)
- Handles empty output with an error response

### 4.3 Agent (Python)

**agent_cli.py**

- Parses `--session_id` and `--message`
- Loads/saves conversation history in SQLite (`hotel_agent.db`)
- Calls `HotelConciergeAgent.process_input(message)`
- Prints the result as JSON

**agent.py**

- **HotelConciergeAgent**:
  - Uses OpenAI-compatible API (OpenAI, Groq, etc.)
  - System prompt from `system_prompt.md`
  - Defines tools: `search_hotels`, `show_hotel_details`, `book_room`, `cancel_reservation`, `recommend_activities`
  - Handles tool calls: executes functions, feeds results back to the LLM, then returns the final reply and `ui_action`

**tools.py**

- Implements the actual functions:
  - `search_hotels(city, ...)` — returns hotels in a city
  - `show_hotel_details(hotel_id)` — hotel info
  - `book_room(...)` — creates a reservation
  - `cancel_reservation(reservation_id)`
  - `recommend_activities(city)`

---

## 5. How the Chatbot Integrates with the Website

1. **Floating widget**: The chat is a floating panel in the bottom-right, always available without leaving the main page.

2. **Shared state**: When the user asks for hotels in a city:
   - The agent calls `search_hotels(city)`
   - The response includes `ui_action: { filter_city: "Paris" }`
   - The frontend updates the city filter and shows the matching hotel cards

3. **Hotel cards**: Users can:
   - Ask for hotels in chat
   - See results in the grid
   - Click “Book This Room” to prefill the chat with a booking message

4. **Conversation memory**: Each session keeps full chat history in SQLite so the agent remembers context (e.g. which hotel the user chose).

---

## 6. Agentic AI in This Project

- **LLM decides what to do**: The model chooses when to call tools based on the user’s message.
- **Tools = actions**: `search_hotels`, `book_room`, etc. let the chatbot act on hotel data.
- **Loop**: The agent can call multiple tools and ask for more info before answering.
- **UI feedback**: The response can include `ui_action` so the website updates (filter, details) in sync with the conversation.

---

## 7. File Summary

| File               | Role                                          |
| ------------------ | --------------------------------------------- |
| `index.html`       | React UI, chat widget, hotel cards, API calls |
| `api.php`          | HTTP API that invokes the Python agent        |
| `agent_cli.py`     | CLI entry point, session handling             |
| `agent.py`         | `HotelConciergeAgent`, LLM + tool loop        |
| `tools.py`         | Tool implementations (search, book, etc.)     |
| `system_prompt.md` | LLM instructions and behavior                 |
| `hotel_agent.db`   | SQLite DB for sessions and reservations       |

---

## 8. Requirements

- PHP (XAMPP or similar)
- Python 3 with: `openai`, `python-dotenv`, `sqlite3` (built-in)
- `.env` with `OPENAI_API_KEY` (and optional `OPENAI_BASE_URL`, `OPENAI_MODEL_NAME`)
