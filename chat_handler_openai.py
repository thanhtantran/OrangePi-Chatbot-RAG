import time
import json
import requests
from langchain.prompts import PromptTemplate

class ChatHandler:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8080/v1"  # API tương thích OpenAI
        self.temperature = 0.8
        
        try:
            # Kiểm tra kết nối và lấy thông tin model từ máy chủ
            response = requests.get(f"{self.base_url}/models")
            if response.status_code == 200:
                models_data = response.json()
                if models_data and "data" in models_data and len(models_data["data"]) > 0:
                    self.model_name = models_data["data"][0]["id"]
                else:
                    self.model_name = "Qwen2.5-7B-Instruct"  # Fallback nếu không lấy được
                print(f"Successfully connected to server with model: {self.model_name}")
            else:
                self.model_name = "Qwen2.5-7B-Instruct"  # Fallback nếu không kết nối được
                print(f"Could not retrieve model information, using default: {self.model_name}")
            
            # Định nghĩa system message mặc định
            self.system_message = """Bạn là một trợ lý AI hữu ích, nhiệm vụ của bạn là trả lời câu hỏi dựa trên ngữ cảnh được cung cấp.
            
            Nếu ngữ cảnh không chứa thông tin để trả lời câu hỏi, hãy nói "Tôi không tìm thấy thông tin về điều này trong tài liệu."
            """
            
            # Đánh dấu là đã sẵn sàng
            self.client_ready = True
            
        except Exception as e:
            print(f"Error initializing connection: {str(e)}")
            self.client_ready = False
    
    def test_model_generation(self, prompt="Xin chào, bạn là ai?"):
        """
        Test khả năng sinh văn bản của model
        
        Args:
            prompt (str): Prompt để kiểm tra
            
        Returns:
            str: Văn bản được sinh ra, hoặc thông báo lỗi
        """
        if not self.client_ready:
            return "Cannot test model because connection was not initialized successfully."
        
        try:
            start_time = time.time()
            
            # Chuẩn bị dữ liệu yêu cầu chat completions
            request_data = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "Bạn là một trợ lý AI hữu ích."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.temperature
            }
            
            # Gửi yêu cầu tới API chat completions
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                print(f"Response time: {end_time - start_time:.2f} seconds")
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error: API returned status code {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"Error testing model: {str(e)}"
    
    def get_answer(self, question, context):
        """
        Lấy câu trả lời cho câu hỏi dựa trên ngữ cảnh
        
        Args:
            question (str): Câu hỏi
            context (str): Ngữ cảnh
            
        Returns:
            str: Câu trả lời hoặc thông báo lỗi
        """
        if not self.client_ready:
            return "Cannot answer because connection was not initialized successfully."
        
        try:
            # Chuẩn bị tin nhắn với ngữ cảnh và câu hỏi
            user_content = f"""Ngữ cảnh:
            {context}
            
            Câu hỏi: {question}"""
            
            # Chuẩn bị dữ liệu yêu cầu
            request_data = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": user_content}
                ],
                "temperature": self.temperature
            }
            
            # Gửi yêu cầu tới API
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"Error: API returned status code {response.status_code}: {response.text}")
                return "Sorry, I encountered an error while processing your question."
                
        except Exception as e:
            print(f"Error in get_answer: {str(e)}")
            return "Sorry, I encountered an error while processing your question."
    
    def generate_response(self, context, question, chat_history=None):
        """
        Phương thức sinh câu trả lời dựa trên ngữ cảnh, câu hỏi và lịch sử chat
        
        Args:
            context (str): Ngữ cảnh
            question (str): Câu hỏi
            chat_history (list, optional): Lịch sử chat
            
        Returns:
            str: Câu trả lời
        """
        if not self.client_ready:
            return "Cannot generate response because connection was not initialized successfully."
            
        try:
            # Tạo messages từ system, chat history (nếu có) và user question
            messages = [{"role": "system", "content": self.system_message}]
            
            # Thêm lịch sử chat vào messages nếu có
            if chat_history:
                for entry in chat_history:
                    # Giả định chat_history có cấu trúc [[human_message, ai_message], ...]
                    if len(entry) >= 1:
                        messages.append({"role": "user", "content": entry[0]})
                    if len(entry) >= 2:
                        messages.append({"role": "assistant", "content": entry[1]})
            
            # Thêm ngữ cảnh và câu hỏi hiện tại
            user_content = f"""Ngữ cảnh:
            {context}
            
            Câu hỏi: {question}"""
            messages.append({"role": "user", "content": user_content})
            
            # Chuẩn bị dữ liệu yêu cầu
            request_data = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature
            }
            
            # Gửi yêu cầu tới API
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"Error: API returned status code {response.status_code}: {response.text}")
                return "Sorry, I encountered an error while processing your question."
                
        except Exception as e:
            print(f"Error in generate_response: {str(e)}")
            return "Sorry, I encountered an error while processing your question."
    
    def is_ready(self):
        """
        Kiểm tra xem handler đã sẵn sàng để sử dụng chưa
        
        Returns:
            bool: True nếu sẵn sàng, False nếu không
        """
        return self.client_ready