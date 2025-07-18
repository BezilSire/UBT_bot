# UBT Bot

This bot is designed to answer questions about Ubuntium from a knowledge base and respond to each user with memory-like awareness of who they are and what role they play.

## Setup

1.  Install the required libraries:
    ```
    pip install -r requirements.txt
    ```
2.  Place your `firebase_credentials.json` file in the root directory of the project.
3.  Set the `OPENROUTER_API_KEY` environment variable to your OpenRouter API key.
4.  Add your documents to the `data` directory. The documents should be in `.txt` format.

## Running the bot

1.  Process the documents to create the vector store:
    ```
    python ubt-bot/src/scripts/process_documents.py
    ```
2.  Run the bot:
    ```
    python ubt-bot/src/bot.py
    ```

## Updating the knowledge base

To update the knowledge base, simply add or remove documents from the `data` directory and then run the `process_documents.py` script again.
