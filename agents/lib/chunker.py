from typing import List 


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