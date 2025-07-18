import os
from ubt-bot.src.scripts.process_documents import process_documents

def main():
    """
    Updates the knowledge base by processing the documents in the data directory.
    """
    # Get the document paths from the data directory
    document_paths = [os.path.join('data', f) for f in os.listdir('data') if f.endswith('.txt')]
    process_documents(document_paths)

if __name__ == '__main__':
    main()
