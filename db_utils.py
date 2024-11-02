
import sqlite3
from datetime import datetime
import json
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path="conversations.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._get_db() as (conn, cur):
            cur.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    messages TEXT,
                    last_updated TIMESTAMP
                )
            ''')

    @contextmanager
    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn, conn.cursor()
        finally:
            conn.close()

    def save_conversation(self, conversation_id: str, messages: list):
        with self._get_db() as (conn, cur):
            cur.execute(
                '''INSERT OR REPLACE INTO conversations 
                (conversation_id, messages, last_updated) VALUES (?, ?, ?)''',
                (
                    conversation_id,
                    json.dumps(messages),
                    datetime.now().isoformat()
                )
            )
            conn.commit()

    def load_conversation(self, conversation_id: str) -> list:
        with self._get_db() as (conn, cur):
            cur.execute(
                'SELECT messages FROM conversations WHERE conversation_id = ?',
                (conversation_id,)
            )
            result = cur.fetchone()
            return json.loads(result[0]) if result else []

    def get_all_conversations(self):
        with self._get_db() as (conn, cur):
            cur.execute('SELECT conversation_id, last_updated FROM conversations')
            return cur.fetchall()