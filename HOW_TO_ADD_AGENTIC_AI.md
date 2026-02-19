# How to Add Agentic AI to a Project (Like This One)

This guide explains how to add an **agentic AI** chatbot to a web project: the chatbot uses an LLM that can call **tools** (functions) to perform actions in your app, then reply in natural language.

---

## 1. What Is Agentic AI Here?

- **Normal chatbot:** User asks → LLM answers with text only.
- **Agentic chatbot:** User asks → LLM can **call tools** (search DB, create booking, etc.) → uses the results → answers with text and can **trigger UI updates** (e.g. show a list, open a detail page).

You need:

1. **Tools** – Functions the LLM can call (search, book, cancel, etc.).
2. **Agent loop** – Send user message to LLM with tool definitions; if the LLM requests a tool call, run it, feed the result back, and get a final reply.
3. **Backend bridge** – Your website calls an API that runs the agent and returns JSON.
4. **Frontend** – Chat UI that sends messages, shows replies, and reacts to **UI actions** (e.g. filter list, open details).
5. **Session/conversation** – Store chat history so the agent has context.

---

## 2. Prerequisites

- An **LLM API** that supports **tool/function calling** (OpenAI, Groq, Azure OpenAI, etc.).
- A **backend** that can run your agent (e.g. PHP, Node, Python) and optionally run a separate Python process.
- A **frontend** that can send HTTP requests and update the page (React, Vue, or plain JS).

---

## 3. Step-by-Step: Adding Agentic AI

### Step 1: Define Your Tools

List what the agent should be able to do in your app (search, book, cancel, etc.). Each action becomes one **tool**.

**3.1 Implement the functions** (e.g. in `tools.py` or your language):

```python
def search_hotels(city, check_in="", check_out=""):
    # Your logic: DB, API, mock data...
    return [{"id": "h1", "name": "Hotel A", "city": city, ...}]

def book_room(hotel_id, room_type, customer_name, check_in, check_out):
    # Create reservation, return success or error
    return {"reservation_id": "RES-123", "status": "confirmed"}
```

**3.2 Describe each tool for the LLM** in the format your API expects (OpenAI-style example):

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": "Search for hotels in a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "check_in": {"type": "string", "description": "YYYY-MM-DD"},
                    "check_out": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_room",
            "description": "Book a room at a hotel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hotel_id": {"type": "string"},
                    "room_type": {"type": "string"},
                    "customer_name": {"type": "string"},
                    "check_in": {"type": "string"},
                    "check_out": {"type": "string"}
                },
                "required": ["hotel_id", "room_type", "customer_name", "check_in", "check_out"]
            }
        }
    }
]
```

- Good **descriptions** and **parameter names** help the LLM choose the right tool and arguments.
- Mark only truly required parameters as `"required"`; omit optional ones when the user didn’t provide them.

---

### Step 2: Implement the Agent Loop

The agent:

1. Receives the user message and current conversation history.
2. Calls the LLM with `messages` + `tools`, and `tool_choice="auto"`.
3. If the LLM returns **tool_calls**, for each call:
   - Parse the function name and arguments.
   - Call your corresponding function.
   - Append the result as a **tool** message (with `tool_call_id`) to the conversation.
4. Call the LLM again with the updated messages (and usually `tool_choice="none"` so it only generates a final reply).
5. Return that reply and any **UI actions** you want the frontend to perform.

**Minimal loop (conceptually):**

```python
# 1. Append user message
messages.append({"role": "user", "content": user_input})

# 2. Call LLM with tools
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)
msg = response.choices[0].message
messages.append(assistant_message_with_tool_calls(msg))

# 3. If there are tool calls, execute them
if msg.tool_calls:
    for tc in msg.tool_calls:
        name = tc.function.name
        args = json.loads(tc.function.arguments)
        result = call_your_function(name, args)  # your dispatch
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "name": name,
            "content": json.dumps(result)
        })

    # 4. Second LLM call to get final text
    final = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="none"
    )
    return {"text": final.choices[0].message.content, "ui_action": ui_action}
else:
    return {"text": msg.content}
```

- **Dispatch:** Map `tc.function.name` to your real functions (e.g. `search_hotels`, `book_room`) and pass `args`.
- **ui_action:** While executing tools, build a small dict (e.g. `filter_city`, `show_hotel_details`) that your frontend will use to update the page.

---

### Step 3: Add a Backend API (Bridge)

Your frontend should not call the LLM directly. Use a backend endpoint that:

1. Receives `session_id` and `message` (and optionally other headers/body fields).
2. Runs the agent (same process or subprocess).
3. Returns JSON, e.g. `{ "text": "...", "ui_action": { ... } }`.

**Example with PHP calling Python:**

```php
$data = json_decode(file_get_contents("php://input"));
$session_id = $data->session_id;
$message = $data->message;

$output = shell_exec("python agent_cli.py --session_id \"$session_id\" --message \"$message\"");
echo $output;  // JSON from the agent
```

**Example with Node calling Python:**

```javascript
const { spawn } = require('child_process');
const proc = spawn('python', ['agent_cli.py', '--session_id', sessionId, '--message', message]);
let out = '';
proc.stdout.on('data', (d) => { out += d; });
proc.on('close', () => { res.json(JSON.parse(out)); });
```

The important part is: **one HTTP request per user message**, and the response is the agent’s JSON.

---

### Step 4: Persist Conversation (Sessions)

The agent needs **conversation history** (including tool calls and tool results) so it can remember context (e.g. which hotel the user chose).

- Generate a **session_id** per user or per tab (e.g. `sess_` + random string).
- Before running the agent, **load** the list of messages for that `session_id` (from DB or file).
- After the agent runs, **save** the updated `messages` (and optionally state) for that `session_id`.

In this project, `agent_cli.py` loads/saves conversation from SQLite so each session keeps its own history.

---

### Step 5: Connect the Frontend

**5.1 Chat UI**

- A list of messages (user / assistant).
- An input and a “Send” button.
- On Send: POST `{ session_id, message }` to your API; then append the user message to the list and show a loading state.

**5.2 Handle the response**

- Parse the JSON: `{ text, ui_action? }`.
- Append `text` as the assistant message.
- If `ui_action` is present, update the rest of the UI (e.g. set filters, selected item, open a modal).

**Example (conceptually):**

```javascript
const res = await fetch('/api.php', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id, message: userMsg })
});
const data = await res.json();

setMessages(prev => [...prev, { sender: 'bot', text: data.text }]);
if (data.ui_action) {
  if (data.ui_action.filter_city) setActiveCity(data.ui_action.filter_city);
  if (data.ui_action.show_hotel_details) setSelectedHotelId(data.ui_action.show_hotel_details);
}
```

So: **one response, two effects** – update the chat and update the page (lists, details, etc.).

---

### Step 6: Write a System Prompt

The LLM needs instructions so it uses tools correctly and talks in the right tone.

- List the tools and when to use them.
- Describe the flow (e.g. “When the user says a city, call searchHotels; when they choose a hotel, call showHotelDetails then ask for room and dates”).
- Add rules (e.g. “Never confirm a booking without calling bookRoom”).
- Optionally: “When you call showHotelDetails, the frontend will open that hotel’s page; tell the user to choose a room and send dates and contact info.”

Put this in a **system message** at the start of `messages` (or in a file that you load into the system message, like `system_prompt.md`).

---

## 4. Patterns Used in This Project

| Pattern | What we do |
|--------|------------|
| **Tool → UI action** | When the agent runs `search_hotels(city)`, we return `ui_action: { filter_city: city }` so the frontend filters the list. |
| **Tool → same UI** | When the agent runs `show_hotel_details(hotel_id)`, we return `ui_action: { show_hotel_details: hotel_id }` so the frontend opens that hotel. |
| **Single response** | The API always returns one JSON object: `{ text, ui_action? }`. The frontend never parses tool names; it only reacts to `ui_action`. |
| **Session in backend** | Session ID is generated in the frontend; the backend loads/saves conversation by that ID so the agent has full context. |
| **Sanitize tool args** | We clean optional args (e.g. don’t pass `budget: 0` or `guests: 0` when the user didn’t specify them) so tools behave correctly. |

---

## 5. Checklist for Your Own Project

1. **List actions** the bot should perform (search, book, cancel, etc.).
2. **Implement** each action as a function and expose it in a **tools** array (name + parameters + descriptions).
3. **Implement the agent loop**: user message → LLM with tools → execute requested tools → append tool results → final LLM call → return `{ text, ui_action }`.
4. **Add a backend endpoint** that receives `session_id` + `message`, runs the agent, returns JSON.
5. **Persist conversation** per `session_id` and pass it into the agent each time.
6. **Build a chat UI** that POSTs messages and displays `text`; handle `ui_action` to update the rest of the app.
7. **Write a system prompt** that describes tools, flow, and rules.
8. **Optional:** Add error handling (e.g. agent crashes → return `{ "text": "Something went wrong." }` so the frontend always gets valid JSON).

---

## 6. Tech Alternatives

- **Backend:** Any language (Node, Python FastAPI, PHP, etc.) can run the agent or call a Python script; the important part is a single endpoint that returns `{ text, ui_action }`.
- **LLM:** Any API that supports function/tool calling (OpenAI, Groq, Anthropic, Azure, etc.); adapt the tool schema to that API’s format.
- **Frontend:** React, Vue, Svelte, or vanilla JS; the pattern is the same: send message → show `text` → apply `ui_action`.
- **Session store:** SQLite, Redis, or in-memory; the agent only needs the list of messages (and optionally state) keyed by `session_id`.

---

## 7. Summary

To add agentic AI to a project like this one:

1. **Define tools** (functions + schema for the LLM).
2. **Implement the agent loop** (LLM + tool execution + optional second LLM call for final reply).
3. **Expose an API** that runs the agent and returns `{ text, ui_action }`.
4. **Persist conversation** per session.
5. **Connect the frontend**: chat UI + handling of `ui_action` to update the page.
6. **Guide the LLM** with a clear system prompt.

The chatbot then both **talks** and **acts** (via tools), and the UI stays in sync using `ui_action`.
