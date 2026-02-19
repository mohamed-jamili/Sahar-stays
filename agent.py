# =============================================================================
# Hotel Concierge Agent: LLM with tool calling. Receives user message,
# optionally runs tools (search_hotels, book_room, etc.), returns text + ui_action.
# =============================================================================

import os
import json
import sys
# Load .env so we can read OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL_NAME
from dotenv import load_dotenv

load_dotenv()

# OpenAI client (works with OpenAI, Groq, or any compatible API when base_url is set)
from openai import OpenAI
# All tools the agent can call (implemented in tools.py)
from tools import search_hotels, show_hotel_details, book_room, cancel_reservation, modify_reservation, recommend_activities


class HotelConciergeAgent:
    """Agent that uses an LLM and a set of tools to handle hotel search and booking."""

    def __init__(self, history=None):
        # Create API client: key and optional base_url (e.g. for Groq or local LLM)
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")  # Optional: for Groq, LocalAI, etc.
        )
        # Model name (e.g. gpt-4o, or provider-specific)
        self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")

        # Load system prompt from file (instructions for the LLM)
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        # Messages list: either restored from history or start with system message only
        if history:
            self.messages = history
        else:
            self.messages = [
                {"role": "system", "content": self.system_prompt}
            ]

        # Tool definitions in OpenAI function-calling format (name, description, parameters)
        self.tools = [
            # Tool 1: search hotels by city and optional filters
            {
                "type": "function",
                "function": {
                    "name": "search_hotels",
                    "description": "Search for hotels based on criteria.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "City to search (required)"},
                            "check_in": {"type": "string", "description": "Check-in date YYYY-MM-DD. Omit if not provided."},
                            "check_out": {"type": "string", "description": "Check-out date YYYY-MM-DD. Omit if not provided."},
                            "guests": {"type": "integer", "description": "Number of guests. Omit if not provided."},
                            "budget": {"type": "integer", "description": "Max budget per night. Omit if not provided."},
                            "preferences": {"type": "array", "items": {"type": "string"}, "description": "Amenity preferences. Omit if not provided."}
                        },
                        "required": ["city"]
                    }
                }
            },
            # Tool 2: get full details for one hotel (used to open hotel page in UI)
            {
                "type": "function",
                "function": {
                    "name": "show_hotel_details",
                    "description": "Get detailed information about a specific hotel.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "hotel_id": {"type": "string"}
                        },
                        "required": ["hotel_id"]
                    }
                }
            },
            # Tool 3: create a reservation
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
                            "check_out": {"type": "string"},
                            "email": {"type": "string"},
                            "phone": {"type": "string"}
                        },
                        "required": ["hotel_id", "room_type", "customer_name", "check_in", "check_out"]
                    }
                }
            },
            # Tool 4: cancel a reservation by ID
            {
                 "type": "function",
                 "function": {
                     "name": "cancel_reservation",
                     "description": "Cancel an existing reservation.",
                     "parameters": {
                         "type": "object",
                         "properties": {
                             "reservation_id": {"type": "string"}
                         },
                         "required": ["reservation_id"]
                     }
                 }
            },
            # Tool 5: get activity recommendations for a city
            {
                "type": "function",
                "function": {
                    "name": "recommend_activities",
                    "description": "Get recommendations for activities in a city.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"}
                        },
                        "required": ["city"]
                    }
                }
            }
        ]

    def process_input(self, user_input):
        """Process one user message: call LLM, run tools if requested, return text and ui_action."""
        # Append the user message to conversation history
        self.messages.append({"role": "user", "content": user_input})

        # Step 1: Call LLM with tools; it may return text only or request tool calls
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.messages,
                tools=self.tools,
                tool_choice="auto"  # Let the model decide whether to call tools
            )
        except Exception as e:
            # Handle provider-specific errors (e.g. Groq tool_use_failed)
            if "tool_use_failed" in str(e):
                error_str = str(e)
                city_hint = ""
                if "city" in error_str.lower():
                    import re
                    city_match = re.search(r'"city":\s*"([^"]+)"', error_str)
                    if city_match:
                        city_hint = f" in {city_match.group(1)}"
                return {
                    "text": f"I'd love to help you find hotels{city_hint}! To show you the best options, I'll need your travel dates and number of guests. When are you planning to visit?",
                    "ui_action": {"filter_city": city_match.group(1)} if city_match else {}
                }
            raise e

        message = completion.choices[0].message

        # Build assistant message for history (must include tool_calls if present for API compatibility)
        assistant_msg = {
            "role": "assistant",
            "content": message.content
        }
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                t.model_dump() for t in message.tool_calls
            ]

        self.messages.append(assistant_msg)
        tool_calls = message.tool_calls

        # Step 2: If the model did not request any tools, return its text reply
        if not tool_calls:
            return {"text": message.content}

        # Step 3: Execute each tool call and collect results + ui_action
        ui_action = {}

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            result = None
            if function_name == "search_hotels":
                # Only pass non-empty / meaningful args (avoid budget=0, guests=0, etc.)
                clean_args = {"city": args["city"]}
                if args.get("check_in"):
                    clean_args["check_in"] = args["check_in"]
                if args.get("check_out"):
                    clean_args["check_out"] = args["check_out"]
                if args.get("guests") and args["guests"] > 0:
                    clean_args["guests"] = args["guests"]
                if args.get("budget") and args["budget"] > 0:
                    clean_args["budget"] = args["budget"]
                if args.get("preferences") and len(args["preferences"]) > 0:
                    clean_args["preferences"] = args["preferences"]
                result = search_hotels(**clean_args)
                # Tell frontend to filter hotel list by this city
                ui_action["filter_city"] = args.get("city")
            elif function_name == "show_hotel_details":
                result = show_hotel_details(**args)
                # Tell frontend to open this hotel's detail page
                ui_action["show_hotel_details"] = args.get("hotel_id")
            elif function_name == "book_room":
                result = book_room(**args)
            elif function_name == "cancel_reservation":
                result = cancel_reservation(**args)
            elif function_name == "recommend_activities":
                result = recommend_activities(**args)

            # Append tool result so the LLM can use it in the next turn
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(result)
            })

        # Step 4: Call LLM again with tool results to get final natural-language reply
        try:
            final_completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.messages,
                tools=self.tools,
                tool_choice="none"  # Do not allow more tool calls; just summarize
            )
        except Exception as e:
             if "tool_use_failed" in str(e):
                 return {"text": "I found some results but had trouble summarizing them. Here are the hotels I found: " + json.dumps(ui_action.get('filter_city', '')) }
             print(f"[ERROR] Final completion failed: {e}", file=sys.stderr)
             return {"text": "I encountered an error generating the final response. Please try again."}

        # Return the final text and any ui_action (filter_city, show_hotel_details) for the frontend
        return {
            "text": final_completion.choices[0].message.content,
            "ui_action": ui_action
        }
