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
    # Fetch data based on the new Firebase structure
    total_ubt_earned = db_user.get('total_ubt_earned', 0.0)
    wallet_address = db_user.get('wallet_address', 'Not set') # Renamed from base_payout_address
    vendor_registered = db_user.get('vendor_registered', False)
    payout_ready = db_user.get('payout_ready', False)
    last_payout_timestamp_str = db_user.get('last_payout_timestamp', None) # Expecting ISO string or None

    if last_payout_timestamp_str:
        try:
            # Attempt to parse and format the timestamp nicely if it's a valid ISO string
            # For example, "2023-10-26T10:00:00Z" -> "Oct 26, 2023, 10:00 AM UTC"
            # This requires dateutil.parser or similar robust parsing.
            # For simplicity, just show the string or "Never".
            # from dateutil import parser
            # last_payout_dt = parser.isoparse(last_payout_timestamp_str)
            # last_payout_display = last_payout_dt.strftime("%b %d, %Y, %I:%M %p UTC")
            last_payout_display = last_payout_timestamp_str # Keep as string for now
        except Exception:
            last_payout_display = "N/A (invalid date format)"
    else:
        last_payout_display = "Never"

    transaction_history_message = "📜 Transaction History: (Full history coming soon)"

    wallet_info_parts = [
        f"🤑 *Your Ubuntium Account Status* 🤑\n",
        f"💰 Total UBT Earned (for next payout): *{total_ubt_earned:.2f} UBT*",
    ]

    if wallet_address != 'Not set':
        wallet_info_parts.append(f"🏦 Your Payout Wallet (Base Network):\n`{wallet_address}`")
    else:
        wallet_info_parts.append(
            "⚠️ Your Base payout wallet address is not set. "
            "If you've completed onboarding, this is unusual. Please contact support. "
            "If not, please complete /start to set it up."
        )

    wallet_info_parts.append(f"🏪 Registered as Vendor: {'✅ Yes' if vendor_registered else '❌ No'}")
    wallet_info_parts.append(f"💸 Ready for Next Payout: {'✅ Yes' if payout_ready and total_ubt_earned > 0 else '❌ No'}")
    wallet_info_parts.append(f"🗓️ Last Payout Date: {last_payout_display}")

    wallet_info_parts.append(f"\n{transaction_history_message}")
    wallet_info_parts.append(
        "\n✨ All UBT shown is tracked in our system. "
        "Your 'Total UBT Earned' will be sent to your registered Payout Wallet at the end of each month."
    )

    message_text = "\n".join(wallet_info_parts)

    # Using the main menu keyboard from onboarding module for consistency
    reply_markup = get_main_menu_keyboard()

    await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

# Handlers
wallet_handler = CommandHandler("wallet", check_wallet_command)
check_wallet_button_handler = MessageHandler(Filters.Regex(r"^(💳 Check My Wallet|My Wallet|Wallet)$"), check_wallet_command)
