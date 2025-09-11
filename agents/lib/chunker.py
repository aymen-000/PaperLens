from typing import List 
from flair.models import SequenceTagger
from flair.data import Sentence
from flair.splitter import SegtokSentenceSplitter

class TextChunker : 
    """
        Splits extracted text into chunks for embedding
    """
    
    def __init__(self , chunk_size:int=500 , overlap:int=50):
        
        self.chunk_size = chunk_size
        self.overlap = overlap 
        
        
    def chunk_text(self , text:str) -> List[str] : 
        """Split text into overlappings chunks"""
        
        words = text.split()
        
        chunks = []
        start = 0 
        
        
        while start < len(words) : 
            end = start+ self.chunk_size
            chunk = " ".join(words[start:end])
            
            chunks.append(chunk)
            start += self.chunk_size - self.overlap 
            
        return chunks
    def semantic_splitter(self , text: str) -> List[str]:


        splitter = SegtokSentenceSplitter()
        
        # Split text into sentences
        sentences = splitter.split(text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # Add sentence to the current chunk
            if len(current_chunk) + len(sentence.to_plain_string()) <= self.chunk_size:
                current_chunk += " " + sentence.to_plain_string()
            else:
                # If adding the next sentence exceeds max size, start a new chunk
                chunks.append(current_chunk.strip())
                current_chunk = sentence.to_plain_string()

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

