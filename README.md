# Orangepi-Chatbot-RAG
- 16/04/2025: Đã chạy tốt với DeepSeek API. Bạn cần đăng ký lấy 1 API từ https://platform.deepseek.com
  
Đầu tiên bạn cần tạo 1 file .evn và đưa vào đó  `DEEPSEEK_API_KEY=DeepSeek API của bạn` .

Tạo thêm 1 thư mục là `pdf_documents` và đưa vào đó các file pdf bạn muốn hệ thống đọc và phân tích.

Sau đó chạy ứng dụng bằng lệnh `./start.sh` hoặc cụ thể như sau.
```
# Tạo môi trường ảo và cài đặt dependencies
python -m venv venv

# Kích hoạt môi trường ảo (kiểm tra hệ điều hành)
if [ "$(uname)" == "Darwin" ] || [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    source venv/bin/activate
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ] || [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ]; then
    source venv/Scripts/activate
fi

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng Streamlit
streamlit run app.py --server.fileWatcherType none
```
- 17/04/2025: Nâng cấp sử dụng Google Gemini API và cải thiện xử lý PDF.
  
Đầu tiên bạn cần tạo 1 file .env và đưa vào đó `GEMINI_API_KEY=Gemini API của bạn` (đăng ký tại https://ai.google.dev/).

Tạo thêm 1 thư mục là `pdf_documents` và đưa vào đó các file pdf bạn muốn hệ thống đọc và phân tích. Cài thêm các gói.

```
# Install Tesseract OCR and Vietnamese language data
sudo apt-get update
sudo apt-get install -y tesseract-ocr
sudo apt-get install -y tesseract-ocr-vie
sudo apt-get install -y poppler-utils 
```

Sau đó chạy ứng dụng bằng lệnh `./start.sh`
