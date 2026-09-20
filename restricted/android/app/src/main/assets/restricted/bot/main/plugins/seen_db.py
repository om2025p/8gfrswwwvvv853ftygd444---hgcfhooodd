# Database helper for tracking seen channels across search queries
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'seen_channels.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seen_channels (
            username TEXT PRIMARY KEY,
            title TEXT,
            members INTEGER,
            first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def is_channel_seen(username):
    if not username or not isinstance(username, str):
        return True
    u_clean = username.lower().strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM seen_channels WHERE username = ?', (u_clean,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def get_all_seen_usernames():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM seen_channels')
    rows = cursor.fetchall()
    conn.close()
    return set(r[0] for r in rows)

def mark_channels_as_seen(channels_list):
    # channels_list is a list of tuples: (title, username, members)
    if not channels_list:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for title, username, members in channels_list:
        if username and isinstance(username, str):
            u_clean = username.lower().strip()
            cursor.execute('''
                INSERT OR IGNORE INTO seen_channels (username, title, members)
                VALUES (?, ?, ?)
            ''', (u_clean, str(title or ''), members if members is not None else 0))
    conn.commit()
    conn.close()

def clear_seen_channels():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM seen_channels')
    conn.commit()
    conn.close()

# Auto-initialize table on import
init_db()
