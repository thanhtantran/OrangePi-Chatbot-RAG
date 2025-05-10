import os
import hashlib
import json
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredPDFLoader
from langchain.schema import Document
from datetime import datetime
import pdf2image
import pytesseract
from typing import List
import concurrent.futures
from chromadb.config import Settings

class CustomOCRPDFLoader:
    """Custom loader for OCR processing of PDFs using Tesseract."""
    
    def __init__(self, file_path: str, language: str = "vie"):
        self.file_path = file_path
        self.language = language
    
    def load(self) -> List[Document]:
        """Load PDF and convert to text using OCR."""
        # Convert PDF to images
        images = pdf2image.convert_from_path(self.file_path)
        
        documents = []
        for i, image in enumerate(images):
            # Use pytesseract to extract text with Vietnamese language support
            text = pytesseract.image_to_string(image, lang=self.language)
            
            # Create a Document for each page
            doc = Document(
                page_content=text,
                metadata={
                    "source": self.file_path,
                    "page": i + 1,
                    "total_pages": len(images),
                    "processing_method": "ocr"
                }
            )
            documents.append(doc)
        
        return documents


class PDFProcessor:
    def __init__(self, pdf_folder="pdf_documents", db_directory="db", processed_files_path="processed_files.json"):
        self.pdf_folder = pdf_folder
        self.db_directory = db_directory
        self.processed_files_path = processed_files_path
        
        # Sử dụng thanhtantran/Vietnamese_Embedding_v2 làm model embedding
        self.embeddings = HuggingFaceEmbeddings(
            model_name="thanhtantran/Vietnamese_Embedding_v2"
        )
        
        # Improved text splitting for better context preservation
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["\n\n", "\n", " ", ""],
            length_function=len
        )
        
        self.db = None
        
        # Create directories if they don't exist
        os.makedirs(pdf_folder, exist_ok=True)
        os.makedirs(db_directory, exist_ok=True)
        
        # Load processed files list
        self.processed_files = self._load_processed_files()
        
        # Initialize or load vector store
        self._initialize_db()

    def _get_file_hash(self, filepath):
        """Calculate file hash to check for changes"""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def _load_processed_files(self):
        """Load list of processed files"""
        if os.path.exists(self.processed_files_path):
            with open(self.processed_files_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_processed_files(self):
        """Save list of processed files"""
        with open(self.processed_files_path, 'w') as f:
            json.dump(self.processed_files, f, indent=2)

    def _initialize_db(self):
        """Initialize or load vector store"""
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
    
    def _is_scanned_pdf(self, pdf_path):
        """
        Check if a PDF is likely a scanned document by examining text content.
        Returns True if likely scanned, False otherwise.
        """
        try:
            # Open the PDF with PyMuPDF
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            text_content = 0
            
            # Check first few pages (up to 5 or total pages, whichever is less)
            pages_to_check = min(5, total_pages)
            
            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text()
                text_content += len(text)
            
            doc.close()
            
            # Calculate average text per page
            avg_text_per_page = text_content / pages_to_check
            
            # If very little text is found, it's likely a scanned document
            # Threshold can be adjusted based on your documents
            return avg_text_per_page < 100
            
        except Exception as e:
            print(f"Error checking if PDF is scanned: {str(e)}")
            # Default to non-scanned if we can't determine
            return False

    def process_pdfs(self):
        """Process new or changed PDF files with adaptive loader selection"""
        new_files_processed = False
        
        # Check each file in directory
        for file in os.listdir(self.pdf_folder):
            if file.endswith('.pdf'):
                pdf_path = os.path.join(self.pdf_folder, file)
                try:
                    current_hash = self._get_file_hash(pdf_path)
                
                    # Check if file has been processed or changed
                    if (file not in self.processed_files or 
                        self.processed_files[file]['hash'] != current_hash):
                        
                        print(f"Processing new file: {file}")
                        
                        # Determine if the PDF is scanned
                        is_scanned = self._is_scanned_pdf(pdf_path)
                        
                        if is_scanned:
                            print(f"Detected scanned document: {file}, using OCR processing")
                            # Use our custom OCR loader for scanned documents
                            loader = CustomOCRPDFLoader(
                                pdf_path,
                                language="vie"  # Vietnamese language code for Tesseract
                            )
                        else:
                            print(f"Detected normal PDF: {file}, using PyMuPDF processing")
                            # Use PyMuPDFLoader for regular PDFs
                            loader = PyMuPDFLoader(pdf_path)
                        
                        documents = loader.load()
                        
                        # Add metadata to help with retrieval
                        for doc in documents:
                            doc.metadata["file_name"] = file
                            doc.metadata["source"] = pdf_path
                            doc.metadata["is_scanned"] = is_scanned
                        
                        # Split into chunks
                        splits = self.text_splitter.split_documents(documents)
                        
                        # Add to vector store
                        self.db.add_documents(splits)
                        
                        # Update processed file info
                        self.processed_files[file] = {
                            'hash': current_hash,
                            'processed_date': datetime.now().isoformat(),
                            'num_pages': len(documents),
                            'num_chunks': len(splits),
                            'is_scanned': is_scanned
                        }
                    
                        new_files_processed = True
                except Exception as e:
                    print(f"Error processing file {file}: {str(e)}")
        
        # Save processed files info
        if new_files_processed:
            self._save_processed_files()
            print("Completed processing new PDF files")

    def search_similar(self, query, k=5):
        """Search for similar text passages"""
        return self.db.similarity_search(query, k=k)


class AdaptivePDFProcessor(PDFProcessor):
    """
    Phiên bản nâng cao của PDFProcessor với khả năng tự động điều chỉnh chiến lược tìm kiếm
    dựa trên độ phức tạp của câu hỏi và độ tin cậy của kết quả.
    """
    def __init__(self, pdf_folder="pdf_documents", db_directory="db", processed_files_path="processed_files.json"):
        super().__init__(pdf_folder, db_directory, processed_files_path)
        
        # Cấu hình adaptive
        self.rerank_cache = {}
        self.cache_size = 100
        self.query_complexity_threshold = 8  # Số từ trong câu hỏi để kích hoạt reranking
        self.confidence_threshold = 0.75
        self.use_lightweight_model = True  # Sử dụng mô hình nhẹ cho thiết bị yếu
        
        # Khởi tạo reranker khi cần
        self._reranker = None
        
        # Tối ưu hóa cơ sở dữ liệu vector
        self._optimize_db()
    
    def _optimize_db(self):
        """Tối ưu hóa cài đặt cho cơ sở dữ liệu vector"""
        chroma_settings = Settings(
            anonymized_telemetry=False,
            persist_directory=self.db_directory,
        )
        
        if os.path.exists(self.db_directory):
            self.db = Chroma(
                persist_directory=self.db_directory,
                embedding_function=self.embeddings,
                client_settings=chroma_settings
            )
        else:
            self.db = Chroma(
                persist_directory=self.db_directory,
                embedding_function=self.embeddings,
                client_settings=chroma_settings
            )
    
    def _get_reranker(self):
        """Lazy loading reranker model với quantization nếu có thể"""
        if self._reranker is None:
            try:
                from sentence_transformers import CrossEncoder
                import torch
                
                # Chọn mô hình reranker phù hợp với tài nguyên
                model_name = 'BAAI/bge-reranker-base' if self.use_lightweight_model else 'BAAI/bge-reranker-v2-m3'
                self._reranker = CrossEncoder(model_name)
                
                # Quantize model nếu có thể
                try:
                    if hasattr(torch, 'quantization') and hasattr(self._reranker.model, 'to'):
                        self._reranker.model = torch.quantization.quantize_dynamic(
                            self._reranker.model, {torch.nn.Linear}, dtype=torch.qint8
                        )
                        print("Successfully quantized reranker model")
                except Exception as e:
                    print(f"Quantization not supported: {str(e)}")
                    
            except Exception as e:
                print(f"Error loading reranker: {str(e)}")
                self._reranker = None
        
        return self._reranker
    
    def _get_cache_key(self, query):
        """Tạo khóa cache từ query"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _analyze_query_complexity(self, query):
        """Phân tích độ phức tạp của câu hỏi"""
        words = query.split()
        complexity = len(words)
        
        # Phát hiện câu hỏi phức tạp (tiếng Việt)
        complex_markers = [
            "tại sao", "vì sao", "như thế nào", "bằng cách nào", 
            "giải thích", "phân tích", "so sánh", "đánh giá", 
            "liên quan", "khác nhau", "giống nhau", "ưu điểm", "nhược điểm"
        ]
        
        for marker in complex_markers:
            if marker in query.lower():
                complexity += 3
        
        return complexity
    
    def _rerank_batch(self, query, batch):
        """Rerank một batch nhỏ các documents"""
        reranker = self._get_reranker()
        if not reranker:
            # Trả về batch với điểm số mặc định nếu không có reranker
            return [(doc, 0.5) for doc in batch]
            
        # Chuẩn bị cặp (query, passage)
        pairs = [(query, doc.page_content) for doc in batch]
        
        # Tính điểm tương đồng
        scores = reranker.predict(pairs)
        
        # Trả về cặp (document, score)
        return list(zip(batch, scores))
    
    def search_similar(self, query, k=5):
        """Adaptive search strategy với caching và xử lý song song"""
        # Kiểm tra cache
        cache_key = self._get_cache_key(query)
        if cache_key in self.rerank_cache:
            print("Using cached results")
            return self.rerank_cache[cache_key][:k]
        
        # Phân tích độ phức tạp của câu hỏi
        query_complexity = self._analyze_query_complexity(query)
        print(f"Query complexity: {query_complexity}")
        
        # Tìm kiếm ban đầu với vector embeddings
        try:
            initial_results = self.db.similarity_search_with_relevance_scores(query, k=10)
        except:
            # Fallback nếu không hỗ trợ relevance scores
            initial_results = [(doc, 0.5) for doc in self.db.similarity_search(query, k=10)]
        
        # Kiểm tra độ tin cậy của kết quả
        high_confidence_docs = []
        low_confidence_docs = []
        
        for doc, score in initial_results:
            # Điều chỉnh công thức tính confidence dựa trên loại điểm số
            # Giả sử điểm số cao hơn = tốt hơn
            confidence = score
            
            if confidence >= self.confidence_threshold:
                high_confidence_docs.append(doc)
            else:
                low_confidence_docs.append(doc)
        
        # Quyết định chiến lược
        need_reranking = query_complexity > self.query_complexity_threshold or len(high_confidence_docs) < k
        
        if not need_reranking and len(high_confidence_docs) >= k:
            # Trường hợp đơn giản: Kết quả embedding đã đủ tốt
            print("Using high confidence embedding results (no reranking needed)")
            results = high_confidence_docs[:k]
        else:
            # Trường hợp phức tạp: Cần reranking
            print("Reranking required for better results")
            
            # Lấy tất cả documents để rerank
            docs_to_rerank = [doc for doc, _ in initial_results]
            
            # Kiểm tra xem có thể sử dụng reranker không
            reranker = self._get_reranker()
            if reranker:
                # Chia nhỏ batch để xử lý song song nếu có nhiều kết quả
                if len(docs_to_rerank) > 5:
                    print("Using parallel processing for reranking")
                    batch_size = 5
                    batches = [docs_to_rerank[i:i+batch_size] for i in range(0, len(docs_to_rerank), batch_size)]
                    
                    final_scored_results = []
                    
                    # Xử lý song song các batch
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                        future_to_batch = {
                            executor.submit(self._rerank_batch, query, batch): batch 
                            for batch in batches
                        }
                        
                        for future in concurrent.futures.as_completed(future_to_batch):
                            batch_results = future.result()
                            final_scored_results.extend(batch_results)
                    
                    # Sắp xếp lại tất cả kết quả theo điểm số
                    final_scored_results.sort(key=lambda x: x[1], reverse=True)
                    
                    # Trả về top k documents
                    results = [doc for doc, _ in final_scored_results[:k]]
                else:
                    # Xử lý tuần tự nếu ít kết quả
                    print("Using sequential reranking")
                    pairs = [(query, doc.page_content) for doc in docs_to_rerank]
                    scores = reranker.predict(pairs)
                    
                    scored_results = list(zip(docs_to_rerank, scores))
                    scored_results.sort(key=lambda x: x[1], reverse=True)
                    
                    results = [doc for doc, _ in scored_results[:k]]
            else:
                # Fallback nếu không có reranker
                print("Reranker not available, using embedding results")
                results = docs_to_rerank[:k]
        
        # Lưu vào cache
        self.rerank_cache[cache_key] = results
        
        # Giới hạn kích thước cache
        if len(self.rerank_cache) > self.cache_size:
            oldest_key = next(iter(self.rerank_cache))
            del self.rerank_cache[oldest_key]
        
        return results
    
    def process_pdfs(self):
        """Ghi đè phương thức process_pdfs để thêm thông báo"""
        print("Using Adaptive PDF Processor for document processing")
        super().process_pdfs()
