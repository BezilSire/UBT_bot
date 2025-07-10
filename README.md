# Ubuntium Telegram Bot

This is the official Telegram bot for the Ubuntium (UBT) ecosystem. It serves as an onboarding and utility tool for users across Africa.

## 🎯 Purpose

*   Onboard new users to the Ubuntium ($UBT) ecosystem, collecting essential details including a Base network payout address.
*   Implement a multi-tiered referral program to incentivize user growth, with UBT earnings tracked in Firebase.
*   Allow users to check their tracked `total_ubt_earned`, which is paid out manually by admins monthly to their registered Base `wallet_address`.
*   Register vendors by location and category, and reward referrers if a referred user becomes a vendor.
*   Provide financial education in local languages.
*   Link users to UBT utilities (vendors, swap, resources)
*   Handle frequently asked questions and support
*   Act as a 24/7 smart wallet concierge

## 🛠️ Tech Stack

*   **Bot Framework:** Python (`python-telegram-bot`)
*   **Backend Database:** Firebase (Firestore for user data, vendor info, UBT balances)
*   **Primary Automation:** Jules' native visual builder (conceptual for backend processes like payouts)
*   **AI Language Model:** Google Gemini or other (via API, for future smart replies/NLP tasks)
*   **Environment Management:** `python-dotenv`

## 🚀 Getting Started

### User Prerequisites (for using the bot effectively)
*   A Telegram account.
*   A Base network compatible non-custodial crypto wallet (e.g., MetaMask, Trust Wallet, Coinbase Wallet) to receive monthly UBT payouts. Users will be asked for their Base payout address during onboarding.

### Developer Prerequisites (for running/developing the bot)

*   Python 3.8+
*   Firebase Project (with Firestore enabled)
*   Google AI Studio API Key for Gemini (optional, for future AI features)
*   Telegram Bot Token

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
        *   `ADMIN_CHAT_ID`: Your Telegram user/group ID for admin notifications.
        *   `GEMINI_API_KEY`: Your Google AI Studio API Key for Gemini (optional, for future AI features).

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

## 🌟 Referral Program Details

The Ubuntium bot features a multi-tiered referral program:
*   **Unique Referral Code:** Every user receives a unique code upon onboarding.
*   **Rewards for Referrer (User A) when they refer a New User (User B):**
    *   `+5 UBT`: When User B successfully joins using User A's referral link.
    *   `+2 UBT`: When User B (the new user) adds their Base wallet address during onboarding.
        *   (Note: Since wallet addition is mandatory in current onboarding, this makes the effective reward for a complete direct referral +7 UBT for User A).
    *   `+3 UBT`: If User B later registers their business as a vendor through the bot.
*   **Indirect Referral Bonus (Override Bonus):**
    *   `+1 UBT`: Awarded to User X if User X referred User A, and User A then successfully refers User B. (User X gets a bonus for their referral's successful referral).
*   All UBT rewards are tracked off-chain in Firebase under the user's `total_ubt_earned` field.

## 💰 Payout Process

*   UBT earnings tracked by the bot (e.g., referral rewards) are **not sent automatically** to user wallets.
*   At the **end of each month**, administrators will manually process payouts from the Ubuntium treasury to users' registered Base `wallet_address` based on their `total_ubt_earned`.
*   After payouts, admin processes will reset `total_ubt_earned` to 0 and update `last_payout_timestamp` and `payout_ready` status in Firebase.

## 📊 Firebase Data Structure (Users Collection)

Key fields in each user document within the `users` collection in Firestore:
*   `telegram_id` (String): The user's unique Telegram ID.
*   `username` (String): Telegram username (if available).
*   `name` (String): Full name provided by the user.
*   `phone_number` (String): User's phone number.
*   `location` (Object): Contains `text` and/or `latitude`/`longitude` and `type`.
*   `wallet_address` (String): User's Base network payout address (e.g., from MetaMask, Trust Wallet).
*   `referral_code` (String): This user's unique referral code.
*   `referred_by_code` (String): The referral code of the user who referred them (if any).
*   `total_ubt_earned` (Number): Total UBT accrued by the user, awaiting monthly payout.
*   `referral_count` (Number): Count of direct referrals made by this user.
*   `vendor_registered` (Boolean): `true` if the user has successfully registered a business.
*   `last_payout_timestamp` (Timestamp/String): Timestamp of the last manual payout to this user.
*   `payout_ready` (Boolean): Flag indicating if `total_ubt_earned > 0`. Bot sets to `true` when earnings occur. Admins set to `false` after payout.
*   `onboarding_completed` (Boolean): `true` if the user has completed the onboarding flow.
*   `created_at` (Timestamp/String): Timestamp of user creation.

## Contributing

Contributions are welcome! Please follow standard coding practices and submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details (to be created).