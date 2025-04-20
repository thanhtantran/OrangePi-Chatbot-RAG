from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class ChatHandler:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        self.conversation_memory = []

    def generate_response(self, context, question, chat_history):
        # Tạo context từ lịch sử chat
        conversation_context = "\n".join([
            f"User: {msg['content']}\nAssistant: {msg['assistant_content']}"
            for msg in chat_history[-3:]  # Lấy 3 tương tác gần nhất
            if 'assistant_content' in msg
        ])

        prompt = f"""Dựa vào ngữ cảnh sau đây:

{context}

Lịch sử cuộc hội thoại:
{conversation_context}

Hãy trả lời câu hỏi sau bằng tiếng Việt, có tính đến ngữ cảnh của cuộc hội thoại trước đó:
{question}

Chỉ trả lời dựa trên thông tin có trong ngữ cảnh và lịch sử hội thoại. Nếu không có thông tin, hãy nói rằng bạn không tìm thấy thông tin liên quan."""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Bạn là trợ lý AI giúp trả lời câu hỏi dựa trên nội dung tài liệu PDF bằng tiếng Việt. Hãy trả lời một cách mạch lạc và có tính đến ngữ cảnh của cuộc hội thoại."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Đã xảy ra lỗi khi gọi API: {str(e)}"