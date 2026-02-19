# How to Recreate This Project From Start to End (Beginner Guide)

This guide walks you through building the **Sahar Stays** hotel booking website with an **agentic AI chatbot** from scratch. No prior experience with AI or agents is required—just follow the steps in order.

---

## What You Will Build

- A **website** where users see hotel cards and can filter by city.
- A **chat widget** (floating button) where users talk to an AI concierge.
- The AI can **search hotels**, **show hotel details**, **book rooms**, and **recommend activities**.
- When the user says "Paris", the page shows Paris hotels; when they choose a hotel, the page opens that hotel’s details.

---

## Part 1: What You Need Installed

### 1.1 On Your Computer

| Tool              | What it is                          | How to get it                                                                  |
| ----------------- | ----------------------------------- | ------------------------------------------------------------------------------ |
| **PHP**           | Runs the API that the website calls | Install **XAMPP** (includes PHP + Apache): https://www.apachefriends.org/      |
| **Python 3**      | Runs the AI agent and tools         | https://www.python.org/downloads/ — during install, check "Add Python to PATH" |
| **A code editor** | To write and edit files             | VS Code, Notepad++, or any editor you like                                     |

### 1.2 An LLM API Key

The chatbot uses a **Large Language Model** (e.g. OpenAI or Groq). You need an **API key**:

- **OpenAI (GPT):** https://platform.openai.com/api-keys — create an key and keep it secret.
- **Groq (free tier):** https://console.groq.com/ — create an API key.

You will put this key in a `.env` file later.

---

## Part 2: Project Folder and Structure

### 2.1 Create the Folder

1. Create a new folder, for example: `C:\xampp\htdocs\agentic`  
   (If you use XAMPP, putting the project in `htdocs` lets you open it in the browser as `http://localhost/agentic/`.)

2. All project files will go inside this single folder (no subfolders required for the basic version).

### 2.2 List of Files You Will Create

```
agentic/
├── .env                    ← Your API key (you create this, do not share)
├── index.html              ← The whole website (HTML + CSS + React)
├── api.php                 ← API: receives chat message, calls Python, returns JSON
├── api_hotels.php          ← API: returns list of hotels as JSON
├── api_availability.php    ← API: returns booked dates for a hotel (for calendar)
├── agent_cli.py            ← Entry point: load session, run agent, save session
├── agent.py                ← The AI agent (LLM + tools)
├── tools.py                ← Hotel data and functions: search, book, cancel, etc.
├── system_prompt.md        ← Instructions for the AI (how to behave and when to use tools)
├── get_hotels.py           ← Script that prints hotels as JSON (used by api_hotels.php)
├── setup_db.py             ← Creates the SQLite database and tables
├── main.py                 ← Optional: test the agent in the terminal
└── requirements.txt        ← Python packages to install
```

You can copy these files from an existing project or create them step by step below.

---

## Part 3: Step-by-Step Setup

### Step 1: Install Python Dependencies

1. Open a **terminal** (Command Prompt or PowerShell).
2. Go to your project folder:
   ```bash
   cd C:\xampp\htdocs\agentic
   ```
3. Create `requirements.txt` with this content:
   ```
   openai
   python-dotenv
   ```
4. Run:
   ```bash
   pip install -r requirements.txt
   ```
   This installs the OpenAI client and the library that reads the `.env` file.

---

### Step 2: Create the `.env` File (Your API Key)

1. In the project folder, create a new file named **`.env`** (no other extension).
2. Add one of these, depending on which service you use:

   **If using OpenAI:**

   ```
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL_NAME=gpt-4o
   ```

   **If using Groq:**

   ```
   OPENAI_API_KEY=your-groq-key-here
   OPENAI_BASE_URL=https://api.groq.com/openai/v1
   OPENAI_MODEL_NAME=llama-3.1-70b-versatile
   ```

3. Replace `sk-your-key-here` or `your-groq-key-here` with your real API key.
4. **Important:** Never put `.env` in Git or share it; it contains a secret.

---

### Step 3: Create the Database

1. Create **`setup_db.py`** (see the file in this project—it creates `hotel_agent.db` with two tables: `sessions` and `reservations`).
2. The booking feature needs `room_type`, `check_in`, and `check_out` in the `reservations` table. If your `setup_db.py` does not have them, run this **once** in the same folder after creating the DB:

   ```bash
   python setup_db.py
   ```

   Then open the database and add the missing columns (e.g. with a SQLite browser or Python). Or use this SQL:

   ```sql
   -- If your reservations table was created without these columns, run in SQLite:
   ALTER TABLE reservations ADD COLUMN room_type TEXT;
   ALTER TABLE reservations ADD COLUMN check_in TEXT;
   ALTER TABLE reservations ADD COLUMN check_out TEXT;
   ```

   Or edit `setup_db.py` so the `reservations` table is created with columns:
   `reservation_id`, `hotel_id`, `room_type`, `customer_name`, `check_in`, `check_out`, `status`, `created_at`.

3. Run:
   ```bash
   python setup_db.py
   ```
   You should see: `Database 'hotel_agent.db' created successfully.`

---

### Step 4: Create the Python Files (Backend Logic)

Create these files in the project folder. You can copy them from this project; here is what each one does:

| File                 | Purpose                                                                                                                                                                                                                              |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **tools.py**         | List of hotels (in code) and functions: `search_hotels`, `show_hotel_details`, `book_room`, `cancel_reservation`, `recommend_activities`. Also connects to `hotel_agent.db` for reservations.                                        |
| **agent.py**         | Defines the **HotelConciergeAgent** class: loads the system prompt, defines tools for the LLM, and has `process_input(message)` that calls the LLM, runs any requested tools, and returns `{ "text": "...", "ui_action": { ... } }`. |
| **agent_cli.py**     | Reads `session_id` and `message` from the command line, loads conversation from the database, runs the agent, saves the conversation, and prints the JSON response (so PHP can capture it).                                          |
| **get_hotels.py**    | Imports the hotel list from `tools.py` and prints it as JSON (used by `api_hotels.php`).                                                                                                                                             |
| **system_prompt.md** | Text instructions for the AI: when to search, when to show details, when to book, and how to talk to the user.                                                                                                                       |

**Quick test (optional):** Run the agent in the terminal:

```bash
python main.py
```

Type "Paris" and you should get a reply. Type `quit` to exit.

---

### Step 5: Create the PHP Files (Web API)

The website runs on a server (e.g. XAMPP Apache) and calls these PHP scripts:

| File                     | Purpose                                                                                                                                                                                                                            |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **api.php**              | Receives POST body `{ "session_id": "...", "message": "..." }`. Runs `python agent_cli.py --session_id ... --message "..."` and returns the JSON output (agent response) to the browser.                                           |
| **api_hotels.php**       | Runs `python get_hotels.py` and returns the JSON list of hotels.                                                                                                                                                                   |
| **api_availability.php** | Receives `?hotel_id=h1` (or similar). Runs a Python script that returns booked date ranges (if you have `get_availability.py`). Otherwise the calendar on the hotel details page may stay empty; the rest of the site still works. |

**Important:** PHP must be able to run Python. On Windows with XAMPP, make sure Python is in the system **PATH** so that the command `python` works in the shell.

---

### Step 6: Create the Frontend (index.html)

The file **index.html** contains:

1. **HTML:** A single `<div id="root">` where the app will render.
2. **CSS:** Styles for the page, chat panel, cards, and buttons (in a `<style>` block).
3. **Scripts:** React, ReactDOM, Babel, Tailwind, and Phosphor Icons (loaded from CDNs).
4. **React app (inside `<script type="text/babel">`):**
   - **ChatWidget:** Message list, input, send button; sends POST to `api.php`, displays the reply, and calls `onUiAction(data.ui_action)` when the response includes `ui_action`.
   - **HotelCard:** Shows one hotel (image, name, price, room selector, "Book This Room").
   - **HotelDetails:** Full page for one hotel (image, amenities, calendar, room types with "Select").
   - **App:** Loads hotels from `api_hotels.php`, keeps state (city filter, selected hotel), handles `filter_city` and `show_hotel_details` from `ui_action`, and renders the chat button + ChatWidget.

You can copy **index.html** from this project. The main idea: the chat sends `session_id` and `message` to `api.php`, gets back `{ text, ui_action }`, shows `text` in the chat and uses `ui_action` to update the page (filter by city or open hotel details).

---

## Part 4: Run the Project

### 4.1 Start the Web Server

- **If you use XAMPP:** Start **Apache** from the XAMPP Control Panel.
- Put the project in `C:\xampp\htdocs\agentic`.
- Open in the browser: **http://localhost/agentic/**  
  (or **http://localhost/agentic/index.html**).

### 4.2 If You Don’t Use XAMPP

You can use PHP’s built-in server from the project folder:

```bash
cd C:\xampp\htdocs\agentic
php -S localhost:8000
```

Then open: **http://localhost:8000**

### 4.3 Test the Flow

1. You should see the homepage with "Find Your Perfect Stay" and an "Ask AI Concierge" button.
2. Click the **chat button** (bottom-right) to open the chat.
3. Type **Paris** (or Marrakech, Tokyo, etc.). The AI should answer and the **hotel cards** should filter to that city.
4. Click a hotel card to open **hotel details**.
5. From the chat, say **"I want Le Meurice"** (or another hotel name). The AI should call `show_hotel_details` and the page should open that hotel.
6. Say **"I would like to book the Deluxe Suite at Le Meurice"** and follow the AI’s questions (dates, name, email, phone). It will call `book_room` and confirm.

---

## Part 5: Troubleshooting (Beginner-Friendly)

| Problem                                  | What to check                                                                                                                                                                                 |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **"Agent execution returned no output"** | Python might be crashing. Run in terminal: `python agent_cli.py --session_id test123 --message "hello"` and see if you get JSON. Install dependencies with `pip install -r requirements.txt`. |
| **Chat does not answer**                 | Open the browser **Developer Tools** (F12) → **Network** tab. Send a message and see if the request to `api.php` returns 200 and JSON. Check `.env` and that your API key is valid.           |
| **Hotels do not load**                   | Check **Network** for `api_hotels.php`. Run `python get_hotels.py` in the project folder; it should print a long JSON array.                                                                  |
| **Booking fails or "Room unavailable"**  | The database must have a `reservations` table with columns `room_type`, `check_in`, `check_out`. Add them with the SQL in Step 3 if needed.                                                   |
| **PHP cannot run Python**                | Add Python to the system PATH. In Command Prompt, run `python --version`; if it fails, reinstall Python and check "Add Python to PATH".                                                       |

---

## Part 6: Order of Creation (If You Type Everything Yourself)

If you are recreating the project without copying whole files, a good order is:

1. **requirements.txt** and **.env** (and run `pip install -r requirements.txt`).
2. **setup_db.py** → run it → fix `reservations` schema if needed.
3. **tools.py** (hotels list + all tool functions).
4. **system_prompt.md** (instructions for the AI).
5. **agent.py** (agent class and tool definitions).
6. **agent_cli.py** (load session, run agent, save, print JSON).
7. **get_hotels.py** (print hotels JSON).
8. **api.php**, **api_hotels.php**, **api_availability.php**.
9. **index.html** (copy from the project or build the React parts step by step).
10. **main.py** (optional, for terminal testing).

Then start the server and open the site in the browser.

---

## Summary

- You need **PHP** (e.g. XAMPP), **Python 3**, and an **LLM API key**.
- The **backend** is: PHP APIs that run Python scripts; Python has the **agent** (LLM + tools) and **tools** (hotels + DB).
- The **frontend** is one **index.html** with React: chat sends messages to **api.php**, gets back **text** and **ui_action**, and updates the page (city filter, hotel details).
- **Database:** SQLite with **sessions** (chat history) and **reservations** (bookings); make sure **reservations** has **room_type**, **check_in**, **check_out** for booking to work.

Once this works, you can change the hotel list, add new tools, or adjust the system prompt to change how the AI behaves.
