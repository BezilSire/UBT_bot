import os
from ubt-bot.src.utils.firebase import initialize_firebase, get_user_details, store_user_details
from ubt-bot.src.utils.openrouter import get_openrouter_response
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

def main():
    """
    The main function for the bot.
    """
    # Initialize Firebase
    initialize_firebase()

    # Load the vector store
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory="vector_store", embedding_function=embeddings)

    # Get the user's ID
    user_id = input("Enter your user ID: ")

    # Get the user's details from Firebase
    user_details = get_user_details(user_id)
    if user_details is None:
        # If the user is new, get their details and store them in Firebase
        name = input("Enter your name: ")
        wallet_address = input("Enter your wallet address: ")
        user_details = {"name": name, "wallet_address": wallet_address}
        store_user_details(user_id, user_details)

    # Get the user's query
    query = input("Enter your query: ")

    # Retrieve the most similar documents from the vector store
    docs = db.similarity_search(query, k=3)

    # Construct the prompt
    prompt = f"User details: {user_details}\n\n"
    prompt += "Relevant documents:\n"
    for doc in docs:
        prompt += f"- {doc.page_content}\n"
    prompt += f"\nUser query: {query}"

    # Get the response from the OpenRouter API
    response = get_openrouter_response(prompt)

    # Print the response
    print(response)

if __name__ == '__main__':
    main()
