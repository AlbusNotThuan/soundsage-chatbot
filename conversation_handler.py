# conversation_handler.py
import chainlit as cl
from langchain.schema import AIMessage, HumanMessage
from typing import List, Optional
import json
import os
from datetime import datetime
import uuid
import sqlite3
from contextlib import contextmanager
from db_utils import DatabaseManager

class ConversationHandler:
    def __init__(self):
        self.db = DatabaseManager()

    def generate_conversation_id(self) -> str:
        """Generate a unique conversation ID"""
        return str(uuid.uuid4())

    async def save_messages(self, conversation_id: str, messages: list):
        self.db.save_conversation(conversation_id, messages)

    async def load_messages(self, conversation_id: str) -> list:
        return self.db.load_conversation(conversation_id)

    async def format_history(self, message_history: list) -> str:
        formatted = []
        for msg in message_history:
            role = "Human" if msg.get("type") == "human" else "Assistant"
            formatted.append(f"{role}: {msg.get('content')}")
        return "\n".join(formatted)