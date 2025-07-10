import logging
import os
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    Filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    PicklePersistence # For persisting user_data, chat_data, bot_data
)

# Import handlers from their modules
from bot.handlers import onboarding, referral, vendor, wallet, education, support
from bot.utils.firebase_client import FirebaseClient # Ensure FirebaseClient is imported

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
# Add other env vars like OPENAI_API_KEY if needed later

# Basic logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Use the consistent main menu keyboard from the onboarding module
from bot.handlers.onboarding import get_main_menu_keyboard

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the main menu, using the consistent keyboard."""
    await update.message.reply_text(
        "🏠 Main Menu:",
        reply_markup=get_main_menu_keyboard() # Uses the imported one
    )

# --- Fallback Handlers ---
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles unknown commands."""
    await update.message.reply_text("Sorry, I didn't understand that command. Try /start or /help.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong. The developers have been notified. Please try again later."
        )

def main() -> None:
    """Run the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    # Initialize Firebase Client and add to application.bot_data
    # This makes it globally accessible in handlers via context.bot_data['firebase_client']
    try:
        firebase_client = FirebaseClient() # From bot.utils.firebase_client
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to initialize FirebaseClient in main: {e}", exc_info=True)
        # Depending on severity, you might want to prevent the bot from starting.
        # For now, it will start, but handlers will log errors if firebase_client is needed and missing.
        firebase_client = None # Ensure it's None if init fails

    # Using PicklePersistence for now to save user_data, etc. across restarts.
    # Replace with a more robust persistence solution if needed (e.g., DB-backed).
    persistence = PicklePersistence(filepath='ubuntium_bot_persistence')

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .persistence(persistence)
        .build()
    )

    if firebase_client:
        application.bot_data['firebase_client'] = firebase_client
        logger.info("FirebaseClient successfully added to application.bot_data.")
    else:
        logger.warning("FirebaseClient was not initialized, not adding to application.bot_data. Bot features requiring Firebase will fail.")

    # --- Register Core Command Handlers ---
    application.add_handler(onboarding.start_handler) # /start is crucial. It now resolves if user is new or returning.
    application.add_handler(CommandHandler("menu", main_menu)) # Explicit /menu command

    # --- Register Onboarding Conversation Handler and related buttons ---
    # The main onboarding sequence (Name, Phone, Location) is handled by onboarding_conv_handler
    application.add_handler(onboarding.onboarding_conv_handler)

    # Buttons that might be pressed from the initial /start menu, before entering the conversation,
    # or if the user is already onboarded.
    application.add_handler(onboarding.already_have_wallet_handler)
    # The "Learn About Ubuntium" button from the initial /start screen is handled by the education module directly
    # as specified in onboarding.py (learn_about_handler = MessageHandler(Filters.Regex("^📘 Learn About Ubuntium$"), education.education_command))
    # So, we must ensure that education.education_command_handler or a similar regex handler is added.
    # The onboarding.learn_about_handler is actually what we need if it's defined to point to education.education_command.
    application.add_handler(onboarding.learn_about_handler)


    # --- Register Referral Handlers ---
    application.add_handler(referral.my_referrals_handler) # /myreferrals
    application.add_handler(referral.invite_friends_handler) # Button "My Referrals" or "Invite Friends"

    # --- Register Wallet Handlers ---
    application.add_handler(wallet.wallet_handler) # /wallet
    application.add_handler(wallet.check_wallet_button_handler) # Button "Check My Wallet"

    # --- Register Vendor Handlers (ConversationHandlers) ---
    application.add_handler(vendor.register_vendor_conv_handler)
    application.add_handler(vendor.find_vendor_conv_handler)
    # Also add button handlers if they directly trigger these conversations (already in conv_handler entry_points)

    # --- Register Education Handlers ---
    application.add_handler(education.education_command_handler) # /learn
    application.add_handler(education.education_button_handler) # Button "Learn About Ubuntium"
    for handler in education.education_callback_handlers: # Inline keyboard callbacks
        application.add_handler(handler)

    # --- Register Support Handlers ---
    application.add_handler(support.help_command_handler) # /help
    application.add_handler(support.help_button_handler) # Button "Help"
    for handler in support.support_callback_handlers: # Inline keyboard callbacks
        application.add_handler(handler)
    # Add the specific handler for messages after "Contact Admin" is pressed.
    # This needs to be managed carefully if you have other general text handlers.
    # Consider making the "Contact Admin" part a ConversationHandler too for cleaner state management.
    # For now, it relies on user_data flag set in support.py
    application.add_handler(support.direct_support_message_handler)


    # --- Fallback for unknown commands ---
    application.add_handler(MessageHandler(Filters.COMMAND, unknown_command))

    # --- Error Handler ---
    application.add_error_handler(error_handler)

    logger.info("Ubuntium Bot starting...")
    # Run the bot until the user presses Ctrl-C
    application.run_polling()
    logger.info("Ubuntium Bot shutting down.")

if __name__ == "__main__":
    main()
```
