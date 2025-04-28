import time
from llama_index.llms.ollama import Ollama
from langchain.prompts import PromptTemplate

class ChatHandler:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8080"
        self.model_name = "Qwen2.5-7B-Instruct-rk3588-w8a8-opt-0-hybrid-ratio-0.0"
        self.temperature = 0.8
        
        try:
            # Initialize LLM with the exact parameters from the working example
            self.llm = Ollama(
                model=self.model_name,
                base_url=self.base_url,
                request_timeout=500  # Use the same timeout as the working example
            )
            print(f"Successfully initialized LLM with model: {self.model_name}")
            
            # Define template for prompt
            self.prompt_template = """Bạn là một trợ lý AI hữu ích, nhiệm vụ của bạn là trả lời câu hỏi dựa trên ngữ cảnh được cung cấp.
            
            Ngữ cảnh:
            {context}
            
            Câu hỏi: {question}
            
            Trả lời dựa trên ngữ cảnh được cung cấp. Nếu ngữ cảnh không chứa thông tin để trả lời câu hỏi, hãy nói "Tôi không tìm thấy thông tin về điều này trong tài liệu."
            
            Trả lời:"""
            
        except Exception as e:
            print(f"Error initializing LLM: {str(e)}")
            self.llm = None
    
    def test_model_generation(self, prompt="Xin chào, bạn là ai?"):
        """
        Test the model's text generation capability
        
        Args:
            prompt (str): Prompt to test
            
        Returns:
            str: Generated text, or error message
        """
        if not self.llm:
            return "Cannot test model because LLM was not initialized successfully."
        
        try:
            start_time = time.time()
            response = self.llm.complete(prompt)
            end_time = time.time()
            
            print(f"Response time: {end_time - start_time:.2f} seconds")
            return response.text
        except Exception as e:
            return f"Error testing model: {str(e)}"
    
    def get_answer(self, question, context):
        """
        Get answer to question based on context
        
        Args:
            question (str): Question
            context (str): Context
            
        Returns:
            str: Answer or error message
        """
        if not self.llm:
            return "Cannot answer because LLM was not initialized successfully."
        
        try:
            # Format the prompt with context and question
            formatted_prompt = self.prompt_template.format(
                context=context,
                question=question
            )
            
            # Get response directly using complete
            response = self.llm.complete(formatted_prompt)
            return response.text
        except Exception as e:
            print(f"Error in get_answer: {str(e)}")
            return "Sorry, I encountered an error while processing your question."
    
    def generate_response(self, context, question, chat_history=None):
        """
        Method to generate response based on context, question and chat history
        
        Args:
            context (str): Context
            question (str): Question
            chat_history (list, optional): Chat history
            
        Returns:
            str: Answer
        """
        # Currently we don't use chat_history, but could extend in future
        return self.get_answer(question, context)
    
    def is_ready(self):
        """
        Check if handler is ready to use
        
        Returns:
            bool: True if ready, False if not
        """
        return self.llm is not None
