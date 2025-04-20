# Updated chat_handler.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class ChatHandler:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        # --- THAY ĐỔI Ở ĐÂY ---
        # Di chuyển chỉ dẫn hệ thống vào tham số system_instruction khi khởi tạo model
        system_instruction = "Bạn là trợ lý AI giúp trả lời câu hỏi dựa trên nội dung tài liệu PDF bằng tiếng Việt. Hãy trả lời một cách mạch lạc và có tính đến ngữ cảnh của cuộc hội thoại."
        self.model = genai.GenerativeModel(
            'gemini-1.5-pro',
            system_instruction=system_instruction
        )
        # self.conversation_memory = [] # Biến này hiện chưa được sử dụng trong generate_response

    def generate_response(self, context, question, chat_history):
        # Tạo ngữ cảnh từ lịch sử chat (giữ nguyên logic của bạn)
        conversation_context = "\n".join([
            f"User: {msg['content']}\nAssistant: {msg['assistant_content']}"
            for msg in chat_history[-3:]  # Lấy 3 tương tác cuối
            if 'assistant_content' in msg
        ])

        # Tạo prompt (giữ nguyên logic của bạn)
        prompt = f"""Dựa vào ngữ cảnh sau đây:

{context}

Lịch sử cuộc hội thoại:
{conversation_context}

Hãy trả lời câu hỏi sau bằng tiếng Việt, có tính đến ngữ cảnh của cuộc hội thoại trước đó:
{question}

Chỉ trả lời dựa trên thông tin có trong ngữ cảnh và lịch sử hội thoại. Nếu không có thông tin, hãy nói rằng bạn không tìm thấy thông tin liên quan."""

        try:
            # --- THAY ĐỔI Ở ĐÂY ---
            # Chỉ cần gửi nội dung của người dùng (user prompt)
            # Chỉ dẫn hệ thống đã được thiết lập khi khởi tạo model
            response = self.model.generate_content(
                [
                    # KHÔNG CÒN {"role": "system", ...} ở đây nữa
                    {"role": "user", "parts": [prompt]}
                ]
                # Hoặc cách đơn giản hơn nếu chỉ có một lượt user:
                # response = self.model.generate_content(prompt)
            )
            # Kiểm tra xem response có nội dung không trước khi truy cập text
            # (Một số phiên bản hoặc trường hợp lỗi có thể trả về response không có text)
            if response and response.text:
                 return response.text
            else:
                 # Xử lý trường hợp response trống hoặc không hợp lệ
                 print("Cảnh báo: Gemini API trả về response không có text.")
                 # Có thể trả về lỗi cụ thể hơn hoặc một thông báo mặc định
                 return "Xin lỗi, đã có lỗi xảy ra hoặc không nhận được phản hồi hợp lệ từ AI."

        except Exception as e:
            # Nên log lỗi ra để debug
            print(f"Đã xảy ra lỗi khi gọi Gemini API: {e}")
            return f"Đã xảy ra lỗi khi gọi Gemini API: {str(e)}"