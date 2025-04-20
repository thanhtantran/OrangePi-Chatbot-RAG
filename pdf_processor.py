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
        
        # Use a more powerful multilingual embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
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
