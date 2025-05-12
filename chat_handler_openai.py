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
                    self.model_name = "gemma-3-1b-it-rk3588-w8a8-opt-1-hybrid-ratio-0.0.rkllm"  # Fallback nếu không lấy được
                print(f"Đã kết nối thành công với máy chủ, sử dụng model: {self.model_name}")
            else:
                self.model_name = "gemma-3-1b-it-rk3588-w8a8-opt-1-hybrid-ratio-0.0.rkllm"  # Fallback nếu không kết nối được
                print(f"Không thể lấy thông tin model, sử dụng model mặc định: {self.model_name}")
            
            # Định nghĩa system message mặc định
            self.system_message = """Bạn là một trợ lý AI hữu ích, nhiệm vụ của bạn là trả lời câu hỏi dựa trên ngữ cảnh được cung cấp.
            
            Nếu ngữ cảnh không chứa thông tin để trả lời câu hỏi, hãy nói "Tôi không tìm thấy thông tin về điều này trong tài liệu."
            """
            
            # Tạo session để duy trì kết nối
            self.session = requests.Session()
            self.session.keep_alive = False  # Đóng connection pool để duy trì kết nối dài
            adapter = requests.adapters.HTTPAdapter(max_retries=5)
            self.session.mount('https://', adapter)
            self.session.mount('http://', adapter)
            
            # Đánh dấu là đã sẵn sàng
            self.client_ready = True
            
        except Exception as e:
            print(f"Lỗi khởi tạo kết nối: {str(e)}")
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
            return "Không thể kiểm tra model vì kết nối chưa được khởi tạo thành công."
        
        try:
            start_time = time.time()
            
            # Chuẩn bị dữ liệu yêu cầu chat completions
            request_data = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "Bạn là một trợ lý AI hữu ích."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.temperature,
                "stream": True
            }
            
            # Gửi yêu cầu tới API chat completions
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                headers={'Content-Type': 'application/json', 'Authorization': 'not_required'},
                stream=True,
                verify=False,
                timeout=60
            )
            
            if response.status_code == 200:
                response_text = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            line_text = line.decode('utf-8')
                            if line_text.startswith("data: "):
                                if line_text == "data: [DONE]":
                                    continue
                                line_json = json.loads(line_text.split("data: ")[1])
                                if "choices" in line_json and len(line_json["choices"]) > 0:
                                    if "delta" in line_json["choices"][-1] and "content" in line_json["choices"][-1]["delta"]:
                                        response_text += line_json["choices"][-1]["delta"]["content"]
                        except Exception as e:
                            print(f"Lỗi xử lý dòng: {e}")
                            continue
                
                end_time = time.time()
                print(f"Thời gian phản hồi: {end_time - start_time:.2f} giây")
                return response_text
            else:
                error_msg = f"Lỗi: API trả về mã trạng thái {response.status_code}: {response.text}"
                print(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Lỗi kiểm tra model: {str(e)}"
            print(error_msg)
            return error_msg
    
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
            return "Không thể trả lời vì kết nối chưa được khởi tạo thành công."
        
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
                "temperature": self.temperature,
                "stream": True
            }
            
            # Gửi yêu cầu tới API
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                headers={'Content-Type': 'application/json', 'Authorization': 'not_required'},
                stream=True,
                verify=False,
                timeout=60
            )
            
            if response.status_code == 200:
                response_text = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            line_text = line.decode('utf-8')
                            if line_text.startswith("data: "):
                                if line_text == "data: [DONE]":
                                    continue
                                line_json = json.loads(line_text.split("data: ")[1])
                                if "choices" in line_json and len(line_json["choices"]) > 0:
                                    if "delta" in line_json["choices"][-1] and "content" in line_json["choices"][-1]["delta"]:
                                        response_text += line_json["choices"][-1]["delta"]["content"]
                        except Exception as e:
                            print(f"Lỗi xử lý dòng: {e}")
                            continue
                
                return response_text
            else:
                error_msg = f"Lỗi: API trả về mã trạng thái {response.status_code}: {response.text}"
                print(error_msg)
                return "Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn."
                
        except Exception as e:
            error_msg = f"Lỗi trong get_answer: {str(e)}"
            print(error_msg)
            return "Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn."
    
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
            return "Không thể tạo phản hồi vì kết nối chưa được khởi tạo thành công."
            
        try:
            # Tạo messages từ system, chat history (nếu có) và user question
            messages = [{"role": "system", "content": self.system_message}]
            
            # Thêm lịch sử chat vào messages nếu có
            if chat_history:
                # Xử lý lịch sử chat theo định dạng của dự án
                for msg in chat_history[-3:]:  # Lấy 3 tin nhắn gần nhất
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        messages.append({"role": msg['role'], "content": msg['content']})
            
            # Thêm ngữ cảnh và câu hỏi hiện tại
            user_content = f"""Ngữ cảnh:
            {context}
            
            Câu hỏi: {question}"""
            messages.append({"role": "user", "content": user_content})
            
            # Chuẩn bị dữ liệu yêu cầu
            request_data = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "stream": True
            }
            
            # Gửi yêu cầu tới API với headers và disable SSL verification
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                headers={'Content-Type': 'application/json', 'Authorization': 'not_required'},
                stream=True,
                verify=False,
                timeout=60
            )
            
            if response.status_code == 200:
                response_text = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            line_text = line.decode('utf-8')
                            if line_text.startswith("data: "):
                                if line_text == "data: [DONE]":
                                    continue
                                line_json = json.loads(line_text.split("data: ")[1])
                                if "choices" in line_json and len(line_json["choices"]) > 0:
                                    if "delta" in line_json["choices"][-1] and "content" in line_json["choices"][-1]["delta"]:
                                        response_text += line_json["choices"][-1]["delta"]["content"]
                        except Exception as e:
                            print(f"Lỗi xử lý dòng: {e}")
                            continue
                
                return response_text
            else:
                error_msg = f"Lỗi: API trả về mã trạng thái {response.status_code}: {response.text}"
                print(error_msg)
                return "Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn."
                
        except Exception as e:
            error_msg = f"Lỗi trong generate_response: {str(e)}"
            print(error_msg)
            return "Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn."
    
    def is_ready(self):
        """
        Kiểm tra xem handler đã sẵn sàng để sử dụng chưa
        
        Returns:
            bool: True nếu sẵn sàng, False nếu không
        """
        return self.client_ready