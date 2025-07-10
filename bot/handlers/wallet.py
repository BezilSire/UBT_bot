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
    base_payout_address = db_user.get('base_payout_address', 'Not set')
    # referral_rewards_balance = db_user.get('referral_rewards_balance', 0.0) # This is part of ubt_balance

    transaction_history_message = "Transaction History: (Feature coming soon)"

    wallet_info_parts = [
        f"🤑 *Your Ubuntium Account Status* 🤑\n",
        f"💰 UBT Balance (Tracked for Payout): *{ubt_balance:.2f} UBT*",
    ]

    if base_payout_address != 'Not set':
        wallet_info_parts.append(f"🏦 Your Registered Base Payout Address:\n`{base_payout_address}`")
    else:
        wallet_info_parts.append(
            "⚠️ Your Base payout address is not set. "
            "Please complete onboarding or use a future command to set it up to receive your UBT."
            # TODO: Add a button/command to update/set wallet address if missing post-onboarding
        )

    wallet_info_parts.append(f"\n📜 {transaction_history_message}")
    wallet_info_parts.append(
        "\n✨ All UBT shown here is tracked in our system. "
        "Your total earned UBT will be sent to your registered Base address at the end of each month."
    )

    message_text = "\n".join(wallet_info_parts)

    # Using the main menu keyboard from onboarding module for consistency
    reply_markup = get_main_menu_keyboard()

    await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

# Handlers
wallet_handler = CommandHandler("wallet", check_wallet_command)
check_wallet_button_handler = MessageHandler(Filters.Regex(r"^(💳 Check My Wallet|My Wallet|Wallet)$"), check_wallet_command)
