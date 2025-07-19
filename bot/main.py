import logging
import os
from dotenv import load_dotenv
import firebase_config
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    PicklePersistence
)

# Import handlers from their modules
from bot.handlers import onboarding, referral, vendor, wallet, education, support
from bot.utils.firebase_client import FirebaseClient

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")

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
        reply_markup=get_main_menu_keyboard()
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

async def main() -> None:
    """Run the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    try:
        firebase_client = FirebaseClient()
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to initialize FirebaseClient in main: {e}", exc_info=True)
        firebase_client = None

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

    application.add_handler(onboarding.start_handler)
    application.add_handler(CommandHandler("menu", main_menu))
    application.add_handler(onboarding.onboarding_conv_handler)
    application.add_handler(onboarding.already_have_wallet_handler)
    application.add_handler(onboarding.learn_about_handler)
    application.add_handler(referral.my_referrals_handler)
    application.add_handler(referral.invite_friends_handler)
    application.add_handler(wallet.wallet_handler)
    application.add_handler(wallet.check_wallet_button_handler)
    application.add_handler(vendor.register_vendor_conv_handler)
    application.add_handler(vendor.find_vendor_conv_handler)
    application.add_handler(education.education_command_handler)
    application.add_handler(education.education_button_handler)
    for handler in education.education_callback_handlers:
        application.add_handler(handler)
    application.add_handler(support.help_command_handler)
    application.add_handler(support.help_button_handler)
    for handler in support.support_callback_handlers:
        application.add_handler(handler)
    application.add_handler(support.direct_support_message_handler)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_error_handler(error_handler)

    logger.info("Ubuntium Bot starting...")
    await application.initialize()
    await application.run_polling()
    logger.info("Ubuntium Bot shutting down.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
