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
- 20/04/2025: Nâng cấp sử dụng Google Gemini API và cải thiện xử lý PDF.
  
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

- 28/04/2025: Nâng cấp sử dụng API của RKLLAMA và cải thiện xử lý PDF qua 2 cách, 1 là chỉ sử dụng model embedding, 2 là sử dụng cả model embedding và reranking.

trong file app.py, bạn chỉnh sửa các thư viện theo tùy chọn

`from pdf_processor import PDFProcessor` nếu chỉ sử dụng model embedding, 
`from pdf_processor_rerank import PDFProcessor` sử dụng cả model embedding và reranking

** Lưu ý: nếu chính sửa cách ingest PDF thì phải xóa tát cả nội dung trong thư mục `db` và thư mục `vectorstore` đã tạo ra để ingest lại **
** Xóa hoàn toàn file `processed_files.json` để đọc lại toàn bộ file PDF trong thưc mục  `pdf_documents` **

`from chat_handler_rkllama import ChatHandler` nếu chọn RKLLAMA Local Server là máy chủ thao tác LLM. Bạn phải có máy chủ RKLLAMA Local Server đang chạy ở địa chỉ `http://127.0.0.1:8080`