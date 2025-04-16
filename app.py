import streamlit as st
from datetime import datetime
from pdf_processor import PDFProcessor
from chat_handler import ChatHandler
from chat_history import ChatHistory

st.title("ChatPDF với DeepSeek")

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
