# Ubuntium Telegram Bot

This is the official Telegram bot for the Ubuntium (UBT) ecosystem. It serves as an onboarding and utility tool for users across Africa.

## 🎯 Purpose

*   Onboard new users to the Ubuntium ($UBT) ecosystem
*   Track referrals and reward users
*   Let users check UBT wallet balances
*   Register vendors by location and category
*   Provide financial education in local languages
*   Link users to UBT utilities (vendors, swap, resources)
*   Handle frequently asked questions and support
*   Act as a 24/7 smart wallet concierge

## 🛠️ Tech Stack

*   **Bot Framework:** Python (`python-telegram-bot`)
*   **Backend Database:** Firebase (Firestore)
*   **AI Language Model:** OpenAI GPT (for advanced NLP tasks)
*   **Workflow Automation:** n8n (for backend logic and integrations)
*   **Environment Management:** `python-dotenv`

## 🚀 Getting Started

### Prerequisites

*   Python 3.8+
*   Telegram Account
*   Firebase Project
*   OpenAI API Key (optional, for AI features)
*   n8n instance (optional, for workflow automation)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd ubuntium-telegram-bot
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    *   Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Fill in the required values in your `.env` file:
        *   `TELEGRAM_BOT_TOKEN`: Your Telegram Bot token from BotFather.
        *   `FIREBASE_SERVICE_ACCOUNT_KEY_PATH`: Absolute path to your Firebase Admin SDK JSON key file.
        *   `OPENAI_API_KEY`: Your OpenAI API key.
        *   `ADMIN_CHAT_ID`: Your Telegram user/group ID for admin notifications.
        *   `N8N_WEBHOOK_URL`: Webhook URL for your n8n workflows (if used).

5.  **Set up Firebase:**
    *   Create a Firebase project at [https://console.firebase.google.com/](https://console.firebase.google.com/).
    *   Go to Project settings > Service accounts.
    *   Generate a new private key and save the JSON file. Update `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` in your `.env` file with its path.
    *   Enable Firestore Database in your Firebase project. Set up security rules as needed.

6.  **Run the bot:**
    ```bash
    python -m bot.main
    ```

## 📁 Project Structure

```
ubuntium_bot/
├── bot/
│   ├── __init__.py
│   ├── main.py         # Main application entry point
│   ├── handlers/       # Telegram command and message handlers
│   │   ├── __init__.py
│   │   ├── onboarding.py
│   │   ├── referral.py
│   │   ├── vendor.py
│   │   ├── wallet.py
│   │   ├── education.py
│   │   └── support.py
│   └── utils/          # Utility functions (e.g., Firebase client)
│       ├── __init__.py
│       └── firebase_client.py
├── tests/              # Unit and integration tests
│   └── __init__.py
├── .env                # Local environment variables (ignored by Git)
├── .env.example        # Example environment variables
├── .gitignore          # Files and directories to ignore in Git
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## 🤖 Bot Commands (Initial)

*   `/start` - Initialize the bot and show the main menu.
*   `/help` - Show help information and support options.
*   `/myreferrals` - Check your referral status.
*   `/wallet` - Check your UBT wallet balance.
*   `/findvendor` - Find UBT vendors near you.
*   `/registervendor` - Register your business as a UBT vendor.
*   `/learn` - Access financial education resources.

## Contributing

Contributions are welcome! Please follow standard coding practices and submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details (to be created).