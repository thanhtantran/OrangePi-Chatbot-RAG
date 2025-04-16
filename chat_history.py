import json
from datetime import datetime
import os

class ChatHistory:
    def __init__(self, history_dir="chat_histories"):
        self.history_dir = history_dir
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

    def save_chat(self, session_id, messages):
        filename = f"{self.history_dir}/chat_{session_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    def load_chat(self, session_id):
        filename = f"{self.history_dir}/chat_{session_id}.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def list_chat_sessions(self):
        sessions = []
        if not os.path.exists(self.history_dir):  # Thêm kiểm tra này
            return sessions
        for file in os.listdir(self.history_dir):
            if file.startswith('chat_') and file.endswith('.json'):
                session_id = file[5:-5]  # Remove 'chat_' and '.json'
                with open(f"{self.history_dir}/{file}", 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                    first_message = chat_data[0]['content'] if chat_data else "No messages"
                    sessions.append({
                        'id': session_id,
                        'timestamp': session_id,
                        'preview': first_message[:50] + "..."
                    })
        return sorted(sessions, key=lambda x: x['timestamp'], reverse=True)
