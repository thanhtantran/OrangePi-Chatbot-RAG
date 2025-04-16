import os
import hashlib
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings  # Cập nhật import
from langchain_chroma import Chroma
from datetime import datetime

class PDFProcessor:
    def __init__(self, pdf_folder="pdf_documents", db_directory="db", processed_files_path="processed_files.json"):
        self.pdf_folder = pdf_folder
        self.db_directory = db_directory
        self.processed_files_path = processed_files_path
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.db = None
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(pdf_folder, exist_ok=True)
        os.makedirs(db_directory, exist_ok=True)
        
        # Load danh sách file đã xử lý
        self.processed_files = self._load_processed_files()
        
        # Khởi tạo hoặc load vector store
        self._initialize_db()

    def _get_file_hash(self, filepath):
        """Tính hash của file để kiểm tra thay đổi"""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read(65536)  # Đọc theo chunks
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def _load_processed_files(self):
        """Load danh sách file đã xử lý"""
        if os.path.exists(self.processed_files_path):
            with open(self.processed_files_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_processed_files(self):
        """Lưu danh sách file đã xử lý"""
        with open(self.processed_files_path, 'w') as f:
            json.dump(self.processed_files, f, indent=2)

    def _initialize_db(self):
        """Khởi tạo hoặc load vector store"""
        if os.path.exists(self.db_directory):
            self.db = Chroma(
                persist_directory=self.db_directory,
                embedding_function=self.embeddings
            )
        else:
            self.db = Chroma(
                persist_directory=self.db_directory,
                embedding_function=self.embeddings
            )

    def process_pdfs(self):
        """Xử lý các file PDF mới hoặc đã thay đổi"""
        new_files_processed = False
        
        # Kiểm tra từng file trong thư mục
        for file in os.listdir(self.pdf_folder):
            if file.endswith('.pdf'):
                pdf_path = os.path.join(self.pdf_folder, file)
                try:
                    current_hash = self._get_file_hash(pdf_path)
                
                    # Kiểm tra xem file đã được xử lý chưa hoặc đã thay đổi chưa
                    if (file not in self.processed_files or 
                        self.processed_files[file]['hash'] != current_hash):
                        
                        print(f"Đang xử lý file mới: {file}")
                        
                        # Load và xử lý PDF
                        loader = PyPDFLoader(pdf_path)
                        documents = loader.load()
                        splits = self.text_splitter.split_documents(documents)
                        
                        # Thêm vào vector store
                        self.db.add_documents(splits)
                        
                        # Cập nhật thông tin file đã xử lý
                        self.processed_files[file] = {
                            'hash': current_hash,
                            'processed_date': datetime.now().isoformat(),
                            'num_pages': len(documents)
                        }
                    
                        new_files_processed = True
                except Exception as e:
                    print(f"Lỗi khi xử lý file {file}: {str(e)}")
        
        # Lưu thông tin các file đã xử lý
        if new_files_processed:
            self._save_processed_files()
            #self.db.persist()
            print("Đã hoàn thành việc xử lý các file PDF mới")

    def search_similar(self, query, k=3):
        """Tìm kiếm các đoạn văn bản tương tự"""
        return self.db.similarity_search(query, k=k)
