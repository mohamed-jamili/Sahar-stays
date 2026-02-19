# =============================================================================
# One-time setup: create hotel_agent.db with sessions and reservations tables.
# Run: python setup_db.py
# =============================================================================

import sqlite3


def setup_database():
    conn = sqlite3.connect("hotel_agent.db")
    cursor = conn.cursor()

    # Table: one row per chat session; context = JSON list of messages, state = IDLE/RUNNING
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        context TEXT,
        state TEXT
    )
    """)

    # Table: one row per reservation (booking); used by tools.book_room and check_availability
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id TEXT PRIMARY KEY,
        hotel_id TEXT,
        room_type TEXT,
        customer_name TEXT,
        check_in TEXT,
        check_out TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("Database 'hotel_agent.db' created successfully.")


if __name__ == "__main__":
    setup_database()
