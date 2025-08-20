from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import os
from dotenv import load_dotenv
import pickle

load_dotenv()

class PaperVectorStore:
    def __init__(self, persist_path: str = "faiss_index/faiss_index",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Wrapper around FAISS for storing and searching paper embeddings.
        Args:
            persist_path: Path to store FAISS index on disk
            embedding_model: HuggingFace embedding model name
        """
        self.persist_path = persist_path
        self.embedding_model = HuggingFaceEmbeddings(model_name=embedding_model)
        self.vectorstore = None
        # Load existing index if available
        if os.path.exists(self.persist_path):
            try:
                self.vectorstore = FAISS.load_local(
                    self.persist_path, 
                    self.embedding_model, 
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Failed to load existing FAISS index: {e}")
                self.vectorstore = None

    def _to_documents(self, papers: list[dict]) -> list[Document]:
        """Convert raw papers into LangChain Document objects."""
        return [
            Document(
                page_content=p.get("content", ""),
                metadata={
                    "title": p.get("title", "Untitled"),
                    "id": p.get("id"),
                    "authors": p.get("authors", []),
                    "categories": p.get("categories", []),
                    "url": p.get("url")
                }
            )
            for p in papers
        ]

    def store_papers(self, papers: list[dict]):
        """
        Store papers in FAISS with embeddings (persists to disk).
        """
        docs = self._to_documents(papers)
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents(
                documents=docs,
                embedding=self.embedding_model
            )
        else:
            self.vectorstore.add_documents(docs)
        
        # Persist index to disk using FAISS save_local method
        self.vectorstore.save_local(self.persist_path)
        return f"Stored {len(docs)} papers in FAISS index"

    def similarity_search(self, query: str, k: int = 5):
        """
        Perform similarity search against stored papers.
        """
        if not self.vectorstore:
            raise ValueError("No FAISS index loaded. Call store_papers first.")
        return self.vectorstore.similarity_search(query, k=k)