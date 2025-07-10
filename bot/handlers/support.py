import logging
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

logger = logging.getLogger(__name__)

# Callback data prefixes
FAQ_CALLBACK = "faq_"
CONTACT_ADMIN_CALLBACK = "contact_admin"
BACK_TO_FAQ_CALLBACK = "back_to_faq"
MAIN_MENU_SUPPORT_CALLBACK = "main_menu_support" # For returning to main menu

ADMIN_TELEGRAM_ID = os.getenv("ADMIN_CHAT_ID") # For notifications

FAQ_CONTENT = {
    "what_is_ubt": {
        "question": "❓ What is Ubuntium (UBT)?",
        "answer": "Ubuntium (UBT) is a community-focused digital currency and financial ecosystem designed for Africa. "
                  "It aims to make financial services more accessible, affordable, and empowering for everyone. "
                  "Built on principles of 'Ubuntu' (togetherness), it's money for us, by us!"
    },
    "how_get_ubt": {
        "question": "💰 How do I get UBT?",
        "answer": "You can acquire UBT in several ways:\n"
                  "- **Referrals:** Invite friends using your unique link (from 'My Referrals') and earn UBT when they join.\n"
                  "- **Learn & Earn:** Participate in educational quizzes and tasks within the 'Learn' section (coming soon).\n"
                  "- **Community Tasks:** Look out for announcements on community bounties or projects.\n"
                  "- **Vendor Activities:** Registered vendors might receive bonuses or earn through promotions.\n"
                  "(Direct purchase options may become available in the future)."
    },
    "how_use_wallet": {
        "question": "📱 How to use my UBT wallet?",
        "answer": "Currently, your UBT wallet is managed within this bot. You can:\n"
                  "- Tap 'Check My Wallet' or use /wallet to see your UBT balance.\n"
                  "- View rewards earned from referrals (these are added to your main balance).\n"
                  "Full features like sending/receiving UBT directly and transaction history are planned for future updates."
    },
    "vendor_registration": {
        "question": "🏪 How do I register my business as a vendor?",
        "answer": "It's easy! Tap the 'Register My Business' button on the main menu or type /registervendor. "
                  "The bot will guide you through a few simple steps to provide your business name, location, category, and UBT payment details. "
                  "Once submitted, our team will review your application."
    },
    "find_vendor": {
        "question": "📍 How do I find a UBT vendor?",
        "answer": "Tap the 'Find a UBT Vendor' button on the main menu or type /findvendor. "
                  "You'll be asked to share your location (GPS or by typing your city/area). "
                  "The bot will then show you a list of approved UBT vendors nearby."
    }
}

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /help command and 'Help' or 'Support' button. Shows FAQ options."""
    keyboard_buttons = []
    for key, data in FAQ_CONTENT.items():
        keyboard_buttons.append([InlineKeyboardButton(data["question"], callback_data=f"{FAQ_CALLBACK}{key}")])

    keyboard_buttons.append([InlineKeyboardButton("🧑‍💼 Contact Admin", callback_data=CONTACT_ADMIN_CALLBACK)])
    keyboard_buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data=MAIN_MENU_SUPPORT_CALLBACK)])

    reply_markup = InlineKeyboardMarkup(keyboard_buttons)

    text = "🆘 *Ubuntium Help & Support Center*\n\nChoose an FAQ topic below, or contact an admin if you need further assistance."
    if update.callback_query: # If called from a 'Back to FAQs' button
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_faq_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles FAQ item selection and displays the answer."""
    query = update.callback_query
    await query.answer()

    try:
        faq_key = query.data.split(FAQ_CALLBACK)[1]
    except IndexError:
        logger.error(f"Error splitting FAQ callback data: {query.data}")
        await query.edit_message_text("Sorry, an error occurred. Please try again.", reply_markup=get_main_faq_keyboard()) # a helper for main FAQ keyboard
        return

    faq_item = FAQ_CONTENT.get(faq_key)

    if faq_item:
        message_text = f"*{faq_item['question']}*\n\n{faq_item['answer']}"
        keyboard = [
            [InlineKeyboardButton("⬅️ Back to FAQs", callback_data=BACK_TO_FAQ_CALLBACK)],
            [InlineKeyboardButton("🏠 Main Menu", callback_data=MAIN_MENU_SUPPORT_CALLBACK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        logger.warning(f"FAQ key '{faq_key}' not found from callback: {query.data}")
        await query.edit_message_text("Sorry, I couldn't find information on that topic. Please select from the main FAQ list.", reply_markup=get_main_faq_keyboard())

def get_main_faq_keyboard() -> InlineKeyboardMarkup:
    """Helper function to get the main FAQ keyboard markup."""
    keyboard_buttons = []
    for key, data in FAQ_CONTENT.items():
        keyboard_buttons.append([InlineKeyboardButton(data["question"], callback_data=f"{FAQ_CALLBACK}{key}")])
    keyboard_buttons.append([InlineKeyboardButton("🧑‍💼 Contact Admin", callback_data=CONTACT_ADMIN_CALLBACK)])
    keyboard_buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data=MAIN_MENU_SUPPORT_CALLBACK)])
    return InlineKeyboardMarkup(keyboard_buttons)


async def handle_contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles 'Contact Admin' button. Informs user to type their message."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    user = update.effective_user # user is already defined from query.from_user
    context.user_data['awaiting_support_message'] = True

    # Edit the message to remove inline keyboard and prompt for their message
    await query.edit_message_text(
        text="Okay, you've chosen to contact an admin.\n\n"
             "Please type your full question or issue now in a single message. "
             "I will forward it to the support team.\n\n"
             "They will get back to you as soon as possible (usually via direct Telegram message or in a support group if applicable)."
    )
    # No direct notification to admin yet, wait for user's actual message.

async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles messages after user clicks 'Contact Admin' and is prompted to type."""
    if not context.user_data.get('awaiting_support_message'):
        # This is a general message, not a support follow-up.
        # Guide them to /help if they seem lost, or ignore if bot has other general text handlers.
        # For now, let's assume other handlers might pick this up or it's an unknown command.
        logger.info(f"Received general message from {update.effective_user.id}, not in support flow.")
        # Optionally, you could reply:
        # await update.message.reply_text("If you need help, please use the /help command.")
        return

    user = update.effective_user
    message_text = update.message.text

    logger.info(f"Support message received from user {user.id} ({user.username}): {message_text}")

    admin_message = (
        f"🆘 *New Support Request from Ubuntium Bot* 🆘\n\n"
        f"👤 *User:* {user.full_name} (@{user.username if user.username else 'N/A'}, ID: {user.id})\n"
        f"📞 *User's Contact (if available via bot):* (Bot doesn't have this directly unless collected)\n\n"
        f"💬 *Message:*\n{message_text}"
    )

    if ADMIN_TELEGRAM_ID:
        try:
            await context.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=admin_message, parse_mode='Markdown')
            await update.message.reply_text(
                "✅ Your message has been successfully sent to the admin team.\n"
                "They will review it and get back to you if needed. Thank you for your patience!\n\n"
                "You can now return to the /help menu or use other bot features.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Help Menu", callback_data=BACK_TO_FAQ_CALLBACK)]])
            )
        except Exception as e:
            logger.error(f"Failed to send support message to admin {ADMIN_TELEGRAM_ID}: {e}")
            await update.message.reply_text(
                "⚠️ We encountered a technical issue while sending your message to the admin team. "
                "Please try again in a few moments. If the problem persists, you can also reach out through [alternative support channel/email if available]."
            )
    else:
        logger.warning("ADMIN_CHAT_ID not set. Cannot forward support message.")
        await update.message.reply_text(
            "⚠️ The admin contact system is not fully configured on our end. We apologize for the inconvenience. "
            "Please try again later, or look for alternative contact methods on our official channels."
        )

    context.user_data.pop('awaiting_support_message', None) # Reset flag


async def back_to_faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles 'Back to FAQs' button. Reuses help_command logic for display."""
    # help_command is now designed to handle being called from a callback query.
    await help_command(update, context)

async def handle_main_menu_support_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles 'Main Menu' button press from within support module."""
    query = update.callback_query
    await query.answer()
    from bot.handlers.onboarding import get_main_menu_keyboard as get_reply_main_menu # Ensure correct import

    try:
        await query.edit_message_text(text="Redirecting to main menu...") # Clear inline keyboard
    except Exception as e: # Message might have been deleted or changed
        logger.info(f"Could not edit message on redirect to main menu from support: {e}")

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="🏠 You are back at the Main Menu.",
        reply_markup=get_reply_main_menu() # This sends the ReplyKeyboardMarkup
    )

# Handlers
help_command_handler = CommandHandler("help", help_command)
help_button_handler = MessageHandler(Filters.Regex(r"^(🆘 Help|Support|Bantuan)$"), help_command)

support_callback_handlers = [
    CallbackQueryHandler(handle_faq_selection, pattern=f"^{FAQ_CALLBACK}"),
    CallbackQueryHandler(handle_contact_admin, pattern=f"^{CONTACT_ADMIN_CALLBACK}$"),
    CallbackQueryHandler(back_to_faq_handler, pattern=f"^{BACK_TO_FAQ_CALLBACK}$"),
    CallbackQueryHandler(handle_main_menu_support_callback, pattern=f"^{MAIN_MENU_SUPPORT_CALLBACK}$")
]

# This handler is for messages *after* the user has clicked "Contact Admin"
# It should be added with a group number that gives it priority for users in this state,
# or rely on the fact that other general text handlers are less specific or not present.
# The check `if not context.user_data.get('awaiting_support_message'): return` makes it fairly safe.
direct_support_message_handler = MessageHandler(Filters.TEXT & ~Filters.COMMAND, handle_support_message)
