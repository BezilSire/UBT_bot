import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton # Keep ReplyKeyboardMarkup if needed for menu button
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, Filters
from bot.utils.firebase_client import FirebaseClient # Import FirebaseClient
from bot.handlers.onboarding import get_main_menu_keyboard # For the main menu button

logger = logging.getLogger(__name__)

async def check_wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /wallet command and 'Check My Wallet' button."""
    user = update.effective_user
    user_id_str = str(user.id)
    logger.info(f"User {user_id_str} requested wallet balance.")

    if 'firebase_client' not in context.bot_data:
        logger.error("Firebase client not available in check_wallet_command.")
        try:
            context.bot_data['firebase_client'] = FirebaseClient()
            logger.info("FirebaseClient re-initialized in wallet handler.")
        except Exception as e:
            logger.critical(f"Failed to initialize FirebaseClient in wallet handler: {e}", exc_info=True)
            await update.message.reply_text("Sorry, there's a problem fetching your wallet data. Please try again later.")
            return

    firebase_client: FirebaseClient = context.bot_data['firebase_client']
    db_user = firebase_client.get_user(user_id_str)

    if not db_user:
        logger.warning(f"User {user_id_str} not found in Firebase for wallet command.")
        await update.message.reply_text(
            "I couldn't find your wallet details. Have you completed the /start setup?"
        )
        return

    # Fetch balances from Firebase user document
    # Ensure these field names match what's set during onboarding and referral rewards
    ubt_balance = db_user.get('ubt_balance', 0.0)
    referral_rewards_balance = db_user.get('referral_rewards_balance', 0.0)
    # total_balance = ubt_balance + referral_rewards_balance # Or however you define total

    # Transaction history - Placeholder for now
    # In a real system, transactions would be stored in a subcollection or separate collection in Firebase.
    # For example: /users/{user_id}/transactions/{transaction_id}
    # transactions = firebase_client.get_transactions(user_id_str, limit=5) # Method to be created
    transaction_history_message = "Transaction History: (Coming Soon - No transactions logged yet)"
    # if transactions:
    #     transaction_history_message = "Recent Transactions:\n"
    #     for tx in transactions:
    #         tx_type = tx.get('type', 'N/A').capitalize()
    #         tx_amount = tx.get('amount', 0)
    #         tx_date = tx.get('timestamp', 'N/A') # Assuming timestamp is stored
    #         # Format date nicely if it's a datetime object or ISO string
    #         sign = "+" if tx.get('direction') == "credit" else "-"
    #         transaction_history_message += f"  - {tx_date}: {sign}{tx_amount:.2f} UBT ({tx_type})\n"
    # else:
    #     transaction_history_message = "No recent transactions found."


    message_text = (
        f"🤑 *Your Ubuntium Wallet* 🤑\n\n"
        f"💰 Main Balance: *{ubt_balance:.2f} UBT*\n"
        # f"🎁 Referral Rewards: *{referral_rewards_balance:.2f} UBT*\n" # This is part of main balance now
        # f"📊 Total UBT: *{total_balance:.2f} UBT*\n\n"
        f"{transaction_history_message}\n\n"
        f"✨ All rewards are automatically added to your Main Balance.\n"
        f"(Full wallet features like sending/receiving UBT are coming soon!)"
    )

    # Using the main menu keyboard from onboarding module for consistency
    reply_markup = get_main_menu_keyboard()

    await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

# Handlers
wallet_handler = CommandHandler("wallet", check_wallet_command)
check_wallet_button_handler = MessageHandler(Filters.Regex(r"^(💳 Check My Wallet|My Wallet|Wallet)$"), check_wallet_command)
