import streamlit as st
from datetime import datetime
import time  # Thêm thư viện time để đo thời gian
from pdf_processor import PDFProcessor
from chat_handler_rkllama import ChatHandler
from chat_history import ChatHistory

# Phần đầu của file app.py - thêm vào đầu file
st.set_page_config(
    page_title="ChatPDF với DeepSeek/Gemini/RKLLAMA trên Orange Pi",
    layout="wide",
)

st.markdown("""
<style>
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
    }
    .logo-container {
        text-align: right;
    }
    .logo-img {
        max-height: 60px;
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #f0f2f6;
        padding: 5px 20px;
        text-align: center;
        font-size: 14px;
        border-top: 1px solid #ddd;
        z-index: 999;
    }
    .main-content {
        margin-bottom: 50px; /* Để tránh nội dung bị che bởi footer */
    }
    .timestamp {
        font-size: 12px;
        color: #666;
        margin-top: 5px;
        font-style: italic;
    }
    .response-time {
        font-size: 12px;
        color: #666;
        margin-top: 5px;
        font-style: italic;
        border-top: 1px solid #eee;
        padding-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Header với logo
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.title("ChatPDF với DeepSeek/Gemini/RKLLAMA trên Orange Pi")
with header_col2:
    st.markdown("""
    <div class="logo-container"> <a href="https://orangepi.vn" target="_blank">
        <img src="https://orangepi.vn/wp-content/uploads/2018/05/logo1-1.png" class="logo-img" alt="Logo"></a>
    </div>
    """, unsafe_allow_html=True)

# Đặt phần này vào trong một div để áp dụng margin-bottom
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Khởi tạo session state
if 'processor' not in st.session_state:
    st.session_state.processor = PDFProcessor()
    # Tự động xử lý PDF khi khởi động
    with st.spinner("Đang kiểm tra và xử lý các file PDF mới..."):
        st.session_state.processor.process_pdfs()

if 'chat_handler' not in st.session_state:
    st.session_state.chat_handler = ChatHandler()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = ChatHistory()
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar cho quản lý chat
with st.sidebar:
    st.header("Lịch sử chat")
    if st.button("Tạo cuộc hội thoại mới"):
        st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.rerun()

    # Hiển thị danh sách các phiên chat
    sessions = st.session_state.chat_history.list_chat_sessions()
    for session in sessions:
        preview = session.get('preview', 'Cuộc hội thoại trống')
        if st.sidebar.button(f"Chat {session['timestamp']}: {preview}", key=session['id']):
            st.session_state.current_session_id = session['id']
            st.session_state.messages = st.session_state.chat_history.load_chat(session['id'])
            st.rerun()

# Chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
        # Hiển thị thời gian chat nếu có
        if "timestamp" in message:
            st.markdown(f"<div class='timestamp'>Thời gian: {message['timestamp']}</div>", unsafe_allow_html=True)
        
        # Hiển thị thời gian trả lời nếu có
        if message["role"] == "assistant" and "response_time" in message:
            st.markdown(f"<div class='response-time'>Câu trả lời được tạo ra trong {message['response_time']:.2f} giây</div>", unsafe_allow_html=True)

if question := st.chat_input("Nhập câu hỏi của bạn:"):
    # Thêm câu hỏi vào messages với timestamp
    current_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    st.session_state.messages.append({
        "role": "user", 
        "content": question,
        "timestamp": current_time
    })
    
    with st.chat_message("user"):
        st.write(question)
        st.markdown(f"<div class='timestamp'>Thời gian: {current_time}</div>", unsafe_allow_html=True)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm câu trả lời..."):
            # Bắt đầu đo thời gian
            start_time = time.time()
            
            # Tìm context liên quan
            similar_docs = st.session_state.processor.search_similar(question)
            context = "\n".join([doc.page_content for doc in similar_docs])
            
            # Tạo câu trả lời với context từ lịch sử
            response = st.session_state.chat_handler.generate_response(
                context, 
                question,
                st.session_state.messages
            )
            
            # Kết thúc đo thời gian
            end_time = time.time()
            response_time = end_time - start_time
            
            st.write(response)
            
            # Hiển thị thời gian trả lời
            current_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            st.markdown(f"<div class='timestamp'>Thời gian: {current_time}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='response-time'>Câu trả lời được tạo ra trong {response_time:.2f} giây</div>", unsafe_allow_html=True)
            
            # Lưu thông tin vào messages
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "assistant_content": response,
                "timestamp": current_time,
                "response_time": response_time
            })

            # Lưu lịch sử chat
            st.session_state.chat_history.save_chat(
                st.session_state.current_session_id,
                st.session_state.messages
            )

# Đóng div main-content
st.markdown('</div>', unsafe_allow_html=True)

# Footer với Copyright
st.markdown("""
<div class="footer">
    © 2025 ChatPDF với DeepSeek/Gemini/RKLLAMA trên Orange Pi - All Rights Reserved - <a href="https://orangepi.vn" target="_blank">Orange Pi Vietnam</a> - - - Nếu bạn thấy mã nguồn này có ích, hãy <a href="https://thanhtan.id.vn" target="_blank">ủng hộ tôi</a>
</div>
""", unsafe_allow_html=True)
