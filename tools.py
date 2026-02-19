# =============================================================================
# Tools: functions the agent can call. Includes in-memory HOTELS list,
# SQLite for reservations/sessions, and all tool implementations.
# =============================================================================

import random
import json

# -----------------------------------------------------------------------------
# Mock hotel database: list of dicts, one per hotel (id, name, city, rating,
# price, room_types, amenities, context, image_url). Used by search and details.
# -----------------------------------------------------------------------------
HOTELS = [
    # Marrakech
    {
        "id": "h1",
        "name": "Riad Jasmine",
        "city": "Marrakech",
        "rating": 4.8,
        "price": 85,
        "room_types": {"Standard": 85, "Suite": 150, "Royal Riad": 300},
        "amenities": ["pool", "breakfast", "wifi", "quiet", "spa"],
        "context": "A peaceful oasis in the medina with a beautiful courtyard pool.",
        "image_url": "https://images.unsplash.com/photo-1560625699-703993169cdb?w=600&q=80"
    },
    {
        "id": "h2",
        "name": "Hotel Sofitel",
        "city": "Marrakech",
        "rating": 4.5,
        "price": 250,
        "room_types": {"Standard": 250, "Deluxe": 350, "Royal Suite": 800},
        "amenities": ["pool", "spa", "luxury", "bar", "gym", "concierge"],
        "context": "Luxury hotel with modern amenities and a large swimming pool.",
        "image_url": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=600&q=80"
    },
    {
        "id": "h3",
        "name": "Medina Hostel",
        "city": "Marrakech",
        "rating": 4.0,
        "price": 25,
        "room_types": {"Dorm Bed": 25, "Private Room": 45},
        "amenities": ["wifi", "rooftop", "social events"],
        "context": "Budget-friendly hostel near the main square.",
        "image_url": "https://images.unsplash.com/photo-1520277739536-ea77c3e80353?w=600&q=80"
    },
    # Paris
    {
        "id": "h4",
        "name": "Le Meurice",
        "city": "Paris",
        "rating": 4.9,
        "price": 800,
        "room_types": {"Superior Room": 800, "Deluxe Suite": 1500, "Penthouse": 5000},
        "amenities": ["luxury", "spa", "michelin dining", "view", "bar"],
        "context": "Historic palace hotel with views of the Tuileries Garden.",
        "image_url": "https://images.unsplash.com/photo-1565031491318-aef52749e30d?w=600&q=80"
    },
    {
        "id": "h5",
        "name": "Mama Shelter Paris East",
        "city": "Paris",
        "rating": 4.2,
        "price": 120,
        "room_types": {"Medium Mama": 120, "Large Mama": 160, "XXL Mama": 250},
        "amenities": ["rooftop", "bar", "modern", "wifi", "design"],
        "context": "Hip and trendy hotel with a lively rooftop bar.",
        "image_url": "https://images.unsplash.com/photo-1550586678-f7b23d9b43e7?w=600&q=80"
    },
    # Tokyo
    {
        "id": "h6",
        "name": "Park Hyatt Tokyo",
        "city": "Tokyo",
        "rating": 4.8,
        "price": 600,
        "room_types": {"Park Room": 600, "Park Suite": 1200, "Governor Suite": 2500},
        "amenities": ["luxury", "pool", "view", "jazz bar", "gym", "spa"],
        "context": "Iconic luxury hotel with stunning views of the city skyline.",
        "image_url": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=600&q=80"
    },
    {
        "id": "h7",
        "name": "Shibuya Stream Excel",
        "city": "Tokyo",
        "rating": 4.4,
        "price": 180,
        "room_types": {"Single": 180, "Double": 220, "Corner Twin": 300},
        "amenities": ["modern", "wifi", "convenient", "river view"],
        "context": "Directly connected to Shibuya Station with modern design.",
        "image_url": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=600&q=80"
    },
    # New York
    {
        "id": "h8",
        "name": "The Plaza",
        "city": "New York",
        "rating": 4.7,
        "price": 950,
        "room_types": {"Plaza Room": 950, "Signature Suite": 2000, "Royal Suite": 10000},
        "amenities": ["luxury", "afternoon tea", "central park view", "spa", "butler"],
        "context": "Legendary hotel at the edge of Central Park.",
        "image_url": "https://images.unsplash.com/photo-1562133567-b6a0a9c7cd3d?w=600&q=80"
    },
    {
        "id": "h9",
        "name": "Ace Hotel New York",
        "city": "New York",
        "rating": 4.3,
        "price": 250,
        "room_types": {"Small": 250, "Medium": 350, "Loft Suite": 600},
        "amenities": ["trendy", "bar", "coffee shop", "wifi", "live music"],
        "context": "Cool, retro-chic hotel in Midtown Manhattan.",
        "image_url": "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?w=600&q=80"
    },
    # London
    {
        "id": "h10",
        "name": "The Savoy",
        "city": "London",
        "rating": 4.8,
        "price": 700,
        "room_types": {"Superior Queen": 700, "River View Deluxe": 1100, "Personality Suite": 2500},
        "amenities": ["luxury", "history", "river view", "bar", "pool"],
        "context": "Famous historic luxury hotel on the Strand.",
        "image_url": "https://images.unsplash.com/photo-1565329921943-7e5350447b08?w=600&q=80"
    }
]

import sqlite3


def get_db_connection():
    """Create and return a connection to hotel_agent.db; rows as dict-like Row objects."""
    conn = sqlite3.connect("hotel_agent.db")
    conn.row_factory = sqlite3.Row
    return conn


def check_availability(hotel_id, room_type, check_in, check_out):
    """
    Return True if this room at this hotel is available for the given dates.
    Checks for overlapping confirmed reservations (same hotel_id + room_type).
    Overlap: (existing_start < new_end) and (existing_end > new_start).
    """
    conn = get_db_connection()
    # Count reservations that overlap with [check_in, check_out)
    query = """
    SELECT count(*) FROM reservations
    WHERE hotel_id = ?
    AND room_type = ?
    AND status = 'confirmed'
    AND (check_in < ? AND check_out > ?)
    """
    cursor = conn.execute(query, (hotel_id, room_type, check_out, check_in))
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0


def search_hotels(city, check_in="", check_out="", guests=1, budget=None, preferences=None):
    """
    Return list of hotels in the given city. Optional filters: budget (max price),
    preferences (amenities). City is required; other params optional.
    """
    results = []
    for hotel in HOTELS:
        if hotel["city"].lower() == city.lower():
            # Skip if over budget when budget is set
            if budget and hotel["price"] > float(budget):
                continue
            # Optional: filter by amenities (preferences list)
            if preferences:
                match = False
                for pref in preferences:
                    if pref in hotel["amenities"]:
                        match = True
                        break
                if not match and "all" not in preferences:
                     pass
            results.append(hotel)
    return results


def show_hotel_details(hotel_id):
    """Return the full hotel dict for the given id, or { error: "Hotel not found" }."""
    for hotel in HOTELS:
        if hotel["id"] == hotel_id:
            return hotel
    return {"error": "Hotel not found"}


def book_room(hotel_id, room_type, customer_name, check_in, check_out, email=None, phone=None):
    """
    Create a reservation if the room is available for those dates.
    Returns { reservation_id, status, message } or { error: "..." } if unavailable.
    """
    if not check_availability(hotel_id, room_type, check_in, check_out):
        return {"error": "Room is defined as unavailable for these dates."}

    reservation_id = f"RES-{random.randint(1000, 9999)}"
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO reservations (reservation_id, hotel_id, room_type, customer_name, check_in, check_out, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (reservation_id, hotel_id, room_type, customer_name, check_in, check_out, "confirmed")
    )
    conn.commit()
    conn.close()
    return {"reservation_id": reservation_id, "status": "confirmed", "message": "Booking successful!"}


def cancel_reservation(reservation_id):
    """Set reservation status to 'cancelled'. Returns success or error dict."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT status FROM reservations WHERE reservation_id = ?", (reservation_id,))
    row = cursor.fetchone()

    if row:
        conn.execute("UPDATE reservations SET status = ? WHERE reservation_id = ?", ("cancelled", reservation_id))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Reservation cancelled"}

    conn.close()
    return {"error": "Reservation not found"}


def modify_reservation(reservation_id, new_check_in, new_check_out):
    """Mock: mark reservation as updated (simplified; no actual date update in this schema)."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT status FROM reservations WHERE reservation_id = ?", (reservation_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"status": "success", "message": "Dates updated"}
    return {"error": "Reservation not found"}


def recommend_activities(city):
    """Return a list of suggested activities for the city (hardcoded per city)."""
    city_lower = city.lower()

    if "marrakech" in city_lower:
        return [
            "Visit Jardin Majorelle",
            "Explore the Souks",
            "Dinner at Jemaa el-Fnaa",
            "Relax in a Hammam"
        ]
    elif "paris" in city_lower:
        return [
            "Visit the Louvre Museum",
            "Climb the Eiffel Tower",
            "Walk along the Seine",
            "Explore Montmartre"
        ]
    elif "tokyo" in city_lower:
        return [
            "Visit Senso-ji Temple",
            "Cross the Shibuya Crossing",
            "Explore Akihabara Electronics Town",
            "Sushi at Tsukiji Outer Market"
        ]
    elif "new york" in city_lower:
        return [
            "Walk through Central Park",
            "See a Broadway Show",
            "Visit the Statue of Liberty",
            "Explore Times Square"
        ]
    elif "london" in city_lower:
        return [
            "Visit the British Museum",
            "See the Tower of London",
            "Walk along the South Bank",
            "Explore Covent Garden"
        ]

    return ["City tour", "Local museum", "Central park", "Shopping district"]
