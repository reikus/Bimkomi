import sqlite3
from typing import Optional, List

DB_NAME = "borrow_reminders.db"

def initialize_database():
    """Initializes the database with the necessary tables."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS borrowed_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_description TEXT NOT NULL,
                borrow_date TEXT NOT NULL,
                contact_phone TEXT NOT NULL,
                reminder_frequency TEXT NOT NULL,
                photo_id TEXT
            )
        ''')
        conn.commit()

def add_item(user_id: int, item_description: str, borrow_date: str, contact_phone: str, reminder_frequency: str, photo_id: Optional[str]):
    """Adds a borrowed item to the database."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO borrowed_items (user_id, item_description, borrow_date, contact_phone, reminder_frequency, photo_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, item_description, borrow_date, contact_phone, reminder_frequency, photo_id))
        conn.commit()

def update_item_status(item_id: int, new_status: str):
    """Updates the status of a borrowed item in the database."""
    # Placeholder for functionality to update item status, if needed
    pass

def get_all_items() -> List[sqlite3.Row]:
    """Retrieves all borrowed items from the database."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM borrowed_items')
        return cursor.fetchall()

def get_items_by_user(user_id: int) -> List[sqlite3.Row]:
    """Retrieves borrowed items for a specific user."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM borrowed_items WHERE user_id = ?', (user_id,))
        return cursor.fetchall()

# Ensure the database is initialized when this module is imported
initialize_database()
