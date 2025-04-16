import streamlit as st
from datetime import datetime
from pdf_processor import PDFProcessor
from chat_handler import ChatHandler
from chat_history import ChatHistory

# Phần đầu của file app.py - thêm vào đầu file
st.set_page_config(
    page_title="ChatPDF với DeepSeek trên Orange Pi",
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
</style>
""", unsafe_allow_html=True)

# Header với logo
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.title("ChatPDF với DeepSeek trên Orange Pi")
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

if question := st.chat_input("Nhập câu hỏi của bạn:"):
    # Thêm câu hỏi vào messages
    st.session_state.messages.append({"role": "user", "content": question})
    
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm câu trả lời..."):
            # Tìm context liên quan
            similar_docs = st.session_state.processor.search_similar(question)
            context = "\n".join([doc.page_content for doc in similar_docs])
            
            # Tạo câu trả lời với context từ lịch sử
            response = st.session_state.chat_handler.generate_response(
                context, 
                question,
                st.session_state.messages
            )
            
            st.write(response)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "assistant_content": response
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
    © 2025 ChatPDF với DeepSeek trên Orange Pi - All Rights Reserved - <a href="https://orangepi.vn" target="_blank">Orange Pi Vietnam</a>
</div>
""", unsafe_allow_html=True)