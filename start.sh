#!/bin/bash

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