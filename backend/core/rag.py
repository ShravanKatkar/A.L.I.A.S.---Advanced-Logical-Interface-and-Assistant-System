import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

class RAGEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("RAG Error: GEMINI_API_KEY missing.")
            return

        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2", google_api_key=self.api_key)
        self.vector_store_path = "chroma_db"
        self.vector_store = Chroma(persist_directory=self.vector_store_path, embedding_function=self.embeddings)
        
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=self.api_key, temperature=0.3)
        self.qa_chain = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=self.vector_store.as_retriever())

    def ingest_document(self, file_path):
        """
        Loads a document (PDF, DOCX, TXT) into the vector store.
        """
        if not os.path.exists(file_path):
             return "File not found."

        try:
            if file_path.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith(".docx"):
                loader = Docx2txtLoader(file_path)
            elif file_path.endswith(".txt"):
                loader = TextLoader(file_path)
            else:
                return "Unsupported file format."

            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = text_splitter.split_documents(documents)
            
            self.vector_store.add_documents(texts)
            return f"Successfully analyzed {os.path.basename(file_path)}."
        except Exception as e:
            return f"Error analyzing document: {e}"

    def query_document(self, query):
        """
        Queries the vector store for an answer.
        """
        try:
            response = self.qa_chain.run(query)
            return response
        except Exception as e:
            return f"RAG Error: {e}"

    def retrieve_context(self, query, k=3):
        """
        Retrieves relevant document chunks from the vector store as context.
        """
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            if not docs:
                return ""
            return "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"[-] RAG Retrieval Error: {e}")
            return ""
