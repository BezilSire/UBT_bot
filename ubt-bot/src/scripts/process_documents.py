import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

def process_documents(document_paths):
    """
    Processes the documents, creates embeddings, and stores them in a Chroma vector store.
    """
    # Read the documents
    documents = []
    for path in document_paths:
        with open(path, 'r') as f:
            documents.append(f.read())

    # Split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.create_documents(documents)

    # Create the embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create the vector store
    db = Chroma.from_documents(texts, embeddings, persist_directory="vector_store")
    db.persist()

if __name__ == '__main__':
    # Get the document paths from the data directory
    document_paths = [os.path.join('data', f) for f in os.listdir('data') if f.endswith('.txt')]
    process_documents(document_paths)
