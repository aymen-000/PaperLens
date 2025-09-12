import os
import base64
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from langchain.schema import Document
from PIL import Image
from io import BytesIO
from agents.prompts.agents_prompts import PAPER_RAG_PROMPT
from langchain_google_genai import ChatGoogleGenerativeAI 
from agents.data.indexing import FAISSIndex
from agents.data.embedding import MultimodalEmbedder 
import numpy as np 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Container for retrieval results"""
    text_documents: List[Document]
    image_base64_data: List[str]  # Changed from Any to str for clarity
    
    
# ===========================
# Image to base 64 
# ===========================   
class ImageProcessor:
    """Handles image processing and base64 conversion"""
    
    @staticmethod
    def get_image_base64(filename: str) -> str:
        """Convert image file to base64 string with proper data URL format"""
        try:
            with open(filename, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{b64}"
        except FileNotFoundError:
            logger.error(f"Image file not found: {filename}")
            return ""
        except Exception as e:
            logger.error(f"Error processing image {filename}: {e}")
            return ""
    
    @staticmethod 
    def b64_to_url(b64: str) -> str:
        """Convert base64 string to data URL format"""
        if b64.startswith("data:image"):
            return b64
        return f"data:image/png;base64,{b64}"
    
    @staticmethod
    def validate_image(base64_data: str) -> bool:
        """Validate base64 image data"""
        try:
            # Remove data URL prefix if present
            if base64_data.startswith("data:image"):
                base64_data = base64_data.split(",", 1)[1]
            
            image_data = base64.b64decode(base64_data)
            Image.open(BytesIO(image_data))
            return True
        except Exception as e:
            logger.warning(f"Image validation failed: {e}")
            return False
        
        
# ========================
# Retriever results 
# ========================

class ScientificPaperRetriever:
    """Handles retrieval of text and images from scientific papers"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.text_emb_size = 384  # Fixed typo: was 'szie'
        self.image_emb_size = 512
        
        # Check if index files exist
        text_index_path = "faiss_index/text_index.faiss"
        image_index_path = "faiss_index/image_index.faiss"
        
        if not os.path.exists(text_index_path):
            raise FileNotFoundError(f"Text index not found: {text_index_path}")
        if not os.path.exists(image_index_path):
            raise FileNotFoundError(f"Image index not found: {image_index_path}")
            
        self.text_index = FAISSIndex(dim=self.text_emb_size, index_path=text_index_path)
        self.images_index = FAISSIndex(dim=self.image_emb_size, index_path=image_index_path)
        
        self.text_index.load()
        self.images_index.load()
        self.embedder = MultimodalEmbedder()
    
    def retrieve_text_context(self, query: str, top_k: int = 5) -> List[Document]:
        """Retrieve relevant text passages from scientific papers"""
        try:
            query_text_emb = np.array(self.embedder.embed_text([query])).astype("float32") 
            text_results = self.text_index.search(query_text_emb[0], top_k) 
            
            # Convert to Document objects
            documents = []
            for result in text_results:
                if isinstance(result, dict) and 'content' in result:
                    doc = Document(
                        page_content=result['content'],
                        metadata=result.get('metadata', {})
                    )
                    documents.append(doc)
                else:
                    logger.warning(f"Unexpected result format: {result}")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving text context: {e}")
            return []
    
    def retrieve_images(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant images from scientific papers"""
        try:
            query_clip_emb = np.array(self.embedder.embed_text_using_clip([query])).astype("float32") 
            image_results = self.images_index.search(query_clip_emb[0], top_k)
            
            valid_results = []
            for res in image_results:
                if res.get("score", 0) > 0.5:
                    valid_results.append(res)
            
            return valid_results
            
        except Exception as e:
            logger.error(f"Error retrieving images: {e}")
            return []
    
    def retrieve_all(self, query: str, text_top_k: int = 5, image_top_k: int = 3) -> RetrievalResult:
        """Retrieve both text and images for the query"""
        try:
            # Retrieve text documents
            text_docs = self.retrieve_text_context(query, text_top_k)
            
            # Retrieve images
            image_results = self.retrieve_images(query, image_top_k)
            
            # Convert images to base64
            image_base64_data = []
            
            for result in image_results:
                # Extract filename/path from result
                image_path = result.get('filename') or result.get('path') or result.get('content')
                
                if image_path:
                    base64_data = self.image_processor.get_image_base64(image_path)
                    if base64_data and self.image_processor.validate_image(base64_data):
                        image_base64_data.append(base64_data)
                    else:
                        logger.warning(f"Failed to process image: {image_path}")
                else:
                    logger.warning(f"No valid image path in result: {result}")
            
            return RetrievalResult(
                text_documents=text_docs,
                image_base64_data=image_base64_data,
            )
            
        except Exception as e:
            logger.error(f"Error in retrieval: {e}")
            return RetrievalResult([], [])


# =============================
# RAG using Gemini 
# =============================

class GeminiProAgent:
    """Gemini Pro LLM agent for scientific paper Q&A"""

    def __init__(self, api_key: str, model_name="gemini-2.0-flash-exp"):  # Updated model name
        if not api_key:
            raise ValueError("API key is required")
        
        os.environ["GOOGLE_API_KEY"] = api_key
        self.model = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
        self.system_prompt = PAPER_RAG_PROMPT

    def create_enhanced_prompt(self, query: str, context_text: str, images_info: str) -> str:
        """Create enhanced prompt with context and image information"""
        prompt = f"""{self.system_prompt}

RETRIEVED CONTEXT:
{context_text}

VISUAL MATERIALS:
{images_info}

RESEARCH QUESTION: {query}

Please provide a comprehensive answer based on the context and visual materials above. 
Include relevant citations and explain your reasoning.
"""
        return prompt

    def format_context(self, retrieval_result: RetrievalResult) -> Tuple[str, str]:
        """Format retrieval results into context strings"""

        # Format text context
        text_context = ""
        for i, doc in enumerate(retrieval_result.text_documents, 1):
            text_context += f"[Source {i}]: {doc.page_content}\n\n"

        # Format image information
        images_info = ""
        if retrieval_result.image_base64_data:
            images_info = f"Retrieved {len(retrieval_result.image_base64_data)} relevant figures/charts:\n"
            for i, _ in enumerate(retrieval_result.image_base64_data, 1):
                images_info += f"[Figure {i}] included in the input.\n"
        else:
            images_info = "No relevant images found for this query."

        return text_context, images_info

    def generate_response(self, query: str, retrieval_result: RetrievalResult) -> Dict[str, Any]:
        """Generate response using Gemini Pro with multimodal capabilities"""
        try:
            # Format context
            text_context, images_info = self.format_context(retrieval_result)

            # Create enhanced prompt
            prompt = self.create_enhanced_prompt(query, text_context, images_info)

            # Prepare multimodal content
            content_parts = [{"type": "text", "text": prompt}]

            # Attach images if available
            for img_b64 in retrieval_result.image_base64_data:
                content_parts.append({"type": "image_url", "image_url": {"url": img_b64}})

            # Build the message
            from langchain_core.messages import HumanMessage
            message = HumanMessage(content=content_parts)

            # Invoke Gemini
            response = self.model.invoke([message])

            return {
                "answer": response.content,
                "context_used": len(retrieval_result.text_documents),
                "images_used": len(retrieval_result.image_base64_data)
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "context_used": 0,
                "images_used": 0
            }


""" # ---- Main test ----
if __name__ == "__main__":
    try:
        # Fixed typo in environment variable name
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        # Initialize agent
        agent = GeminiProAgent(api_key=GOOGLE_API_KEY, model_name="gemini-2.0-flash-exp")
        
        query = "Explain what this paper is about"
        retrieval = ScientificPaperRetriever()
        retrieval_result = retrieval.retrieve_all(query=query, text_top_k=2, image_top_k=1)
        
        response = agent.generate_response(query, retrieval_result)

        print("\n===== MODEL RESPONSE =====")
        print(response["answer"])
        print(f"\nContext documents used: {response['context_used']}")
        print(f"Images used: {response['images_used']}")
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}") """