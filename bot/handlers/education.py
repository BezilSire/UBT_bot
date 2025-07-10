import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

logger = logging.getLogger(__name__)

# Define callback data prefixes for language and topics
LANG_CALLBACK = "edu_lang_"
TOPIC_CALLBACK = "edu_topic_"
BACK_TO_LANG_CALLBACK = "edu_back_lang"
BACK_TO_TOPICS_CALLBACK = "edu_back_topics_" # Append lang

# --- Content (Store this more robustly, e.g., JSON files or Firebase) ---
EDUCATION_CONTENT = {
    "en": {
        "what_is_ubt": {
            "title": "🌍 What is Ubuntium (UBT)?",
            "content": "Ubuntium ($UBT) is a community-focused digital currency and financial ecosystem designed for Africa. "
                       "It aims to empower individuals and communities by providing accessible, transparent, and "
                       "low-cost financial tools and services directly on your phone.\n\n"
                       "Think of it as money *for us, by us*, built on the principles of togetherness ('Ubuntu'). "
                       "It's more than just money; it's a movement for financial freedom and local economic growth.",
            # "image": "https://i.imgur.com/EXAMPLE_UBT_LOGO.png" # Example image URL - remove for now
        },
        "how_to_earn": {
            "title": "💰 How to Earn UBT",
            "content": "You can earn UBT in several exciting ways:\n\n"
                       "1.  **Referrals:** Invite friends to join Ubuntium using your unique referral link. When they sign up, you both get rewarded!\n"
                       "2.  **Learn & Earn:** Participate in educational quizzes and tasks within this bot to earn UBT while you learn (coming soon!).\n"
                       "3.  **Community Engagement:** Take part in community bounties, events, or contribute to projects (details announced periodically).\n"
                       "4.  **Vendor Activities:** Registered vendors might be eligible for special rewards or bonuses for using UBT.\n\n"
                       "Keep an eye on announcements for new earning opportunities!"
        },
        "how_to_refer": {
            "title": "🤝 How to Refer Friends",
            "content": "Referring friends is easy and rewarding:\n\n"
                       "1.  Go to the main menu and tap the '🎁 My Referrals' button.\n"
                       "2.  You'll find your unique referral link there (it looks like `https://t.me/YourBotName?start=ref_YOURCODE`).\n"
                       "3.  Share this link with your friends, family, and social networks.\n"
                       "4.  When someone clicks your link and successfully joins Ubuntium through this bot, you'll automatically receive UBT rewards!\n\n"
                       "The more friends you bring, the more you earn and help grow the Ubuntium community!"
        },
        "why_ubt": {
            "title": "💡 Why Use UBT Instead of Regular Money (Fiat)?",
            "content": "Ubuntium offers several advantages:\n\n"
                       "-   **Lower Fees:** Sending and receiving UBT can be significantly cheaper than traditional bank transfers or mobile money, especially across borders.\n"
                       "-   **Accessibility:** All you need is a basic smartphone with Telegram. No bank account required!\n"
                       "-   **Community Owned & Governed:** UBT is designed for the community. Decisions about its future can be influenced by users, not just central institutions.\n"
                       "-   **Empowerment:** UBT helps keep value within local communities, supporting local businesses and creating new economic opportunities.\n"
                       "-   **Transparency:** Transactions on a blockchain (if UBT is on-chain) can offer more transparency than traditional systems.\n"
                       "-   **Innovation:** Opens doors for new financial products and services tailored to African needs."
        }
    },
    "sw": { # Swahili example
        "what_is_ubt": {
            "title": "🌍 Ubuntium (UBT) ni nini?",
            "content": "Ubuntium ($UBT) ni mfumo wa kifedha wa kidijitali unaolenga jamii, ulioundwa mahususi kwa ajili ya Afrika. "
                       "Lengo lake ni kuwawezesha watu binafsi na jamii kwa kutoa zana na huduma za kifedha zinazopatikana kwa urahisi, uwazi, na gharama nafuu moja kwa moja kwenye simu yako.\n\n"
                       "Fikiria kama pesa *kwa ajili yetu, na sisi wenyewe*, iliyojengwa juu ya misingi ya umoja ('Ubuntu'). "
                       "Ni zaidi ya pesa tu; ni harakati ya uhuru wa kifedha na ukuaji wa uchumi wa ndani.",
        },
        "how_to_earn": {
            "title": "💰 Jinsi ya Kupata UBT",
            "content": "Unaweza kupata UBT kwa njia kadhaa za kusisimua:\n\n"
                       "1.  **Rufaa:** Alika marafiki kujiunga na Ubuntium wakitumia linki yako ya kipekee ya rufaa. Wakijiunga, wote mnapata zawadi!\n"
                       "2.  **Jifunze & Upate:** Shiriki katika maswali na kazi za kielimu ndani ya boti hii ili upate UBT unapojifunza (inakuja hivi karibuni!).\n"
                       "3.  **Ushiriki wa Jamii:** Shiriki katika kazi za jamii, matukio, au changia miradi (maelezo yatatangazwa mara kwa mara).\n"
                       "4.  **Shughuli za Wauzaji:** Wauzaji waliosajiliwa wanaweza kupata zawadi maalum au bonasi kwa kutumia UBT.\n\n"
                       "Fuatilia matangazo kwa fursa mpya za mapato!"
        },
        # ... other topics in Swahili (how_to_refer, why_ubt) can be added similarly
    }
    # Add Shona, Ndebele etc.
}

# Callback data for Main Menu button
MAIN_MENU_CALLBACK = "main_menu_edu"


async def education_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /learn command and 'Learn & Earn' button. Prompts for language."""
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data=f"{LANG_CALLBACK}en")],
        [InlineKeyboardButton("🇸🇼 Swahili", callback_data=f"{LANG_CALLBACK}sw")],
        # [InlineKeyboardButton("🇿🇼 Shona", callback_data=f"{LANG_CALLBACK}sn")], # TODO
        # [InlineKeyboardButton("🇿🇼 Ndebele", callback_data=f"{LANG_CALLBACK}nd")], # TODO
        [InlineKeyboardButton("🏠 Main Menu", callback_data=MAIN_MENU_CALLBACK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # If called from a command, send new message. If from callback (e.g. back to langs), edit.
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "📚 Welcome to the Ubuntium Learning Center!\n\nPlease select your preferred language:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "📚 Welcome to the Ubuntium Learning Center!\n\nPlease select your preferred language:",
            reply_markup=reply_markup
        )

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles language selection and shows topics for that language."""
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split(LANG_CALLBACK)[1]
    context.user_data['education_lang'] = lang_code

    topics = EDUCATION_CONTENT.get(lang_code, EDUCATION_CONTENT["en"]) # Default to English if lang not found

    keyboard = []
    for topic_key, topic_data in topics.items():
        keyboard.append([InlineKeyboardButton(topic_data["title"], callback_data=f"{TOPIC_CALLBACK}{lang_code}_{topic_key}")])
    keyboard.append([InlineKeyboardButton("⬅️ Back to Languages", callback_data=BACK_TO_LANG_CALLBACK)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"Great! You selected {lang_code.upper()}. Choose a topic to learn about:", reply_markup=reply_markup)

async def handle_topic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles topic selection and displays the content."""
    query = update.callback_query
    await query.answer()

    try:
        _, lang_code, topic_key = query.data.split("_", 2) # TOPIC_CALLBACK is "edu_topic_"
    except ValueError:
        logger.error(f"Error splitting callback data for topic: {query.data}")
        await query.edit_message_text("Sorry, there was an error processing your request. Please try again.")
        return

    context.user_data['education_topic'] = topic_key # Store current topic

    content_data = EDUCATION_CONTENT.get(lang_code, {}).get(topic_key)

    if not content_data:
        await query.edit_message_text("Sorry, content for this topic is not available. Please select another topic.")
        return

    message_text = f"*{content_data['title']}*\n\n{content_data['content']}"

    keyboard = [
        [InlineKeyboardButton("⬅️ Back to Topics", callback_data=f"{BACK_TO_TOPICS_CALLBACK}{lang_code}")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data=MAIN_MENU_CALLBACK)],
        # [InlineKeyboardButton("📝 Take Quiz (Earn UBT!)", callback_data=f"quiz_{lang_code}_{topic_key}")], # TODO
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    image_url = content_data.get("image") # Image URL is currently removed from content

    # Simplified image handling: Send new message if image, edit if text-only.
    # No deletion of prior messages for V1 simplicity.
    if image_url:
        try:
            # Delete the message that had the topic buttons, then send a new photo message
            await query.message.delete()
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=image_url,
                caption=message_text, # Max 1024 chars for caption
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error sending education photo for {topic_key}: {e}. Falling back to text.")
            # Fallback: if photo fails, try to edit the original message with text only.
            # This might fail if original message was already deleted or changed.
            try:
                await query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
            except Exception as edit_e:
                logger.error(f"Fallback edit_message_text also failed: {edit_e}. Sending new text message.")
                # Final fallback: send as a new message if edit fails
                await context.bot.send_message(chat_id=query.message.chat_id, text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        # If no image, just edit the current message.
        await query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')


async def back_to_languages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles 'Back to Languages' button. Reuses education_command logic for display."""
    query = update.callback_query
    await query.answer()
    # Call education_command, which now handles being called from a callback query for editing.
    await education_command(update, context)


async def back_to_topics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles 'Back to Topics' button. Reuses handle_language_selection logic."""
    query = update.callback_query
    await query.answer()

    # Extract lang_code from callback_data or user_data as fallback
    try:
        # Pattern for BACK_TO_TOPICS_CALLBACK is "edu_back_topics_LANGCODE"
        lang_code = query.data.split(BACK_TO_TOPICS_CALLBACK)[1] # Gets LANGCODE
    except IndexError:
        lang_code = context.user_data.get('education_lang', 'en') # Fallback

    # To show topics, we essentially re-run the part of language selection that shows topics.
    # For this, we can simulate the callback data that handle_language_selection expects, or call it directly.
    # Let's construct the keyboard directly here for clarity for "back to topics".

    context.user_data['education_lang'] = lang_code # Ensure it's set for consistency
    topics = EDUCATION_CONTENT.get(lang_code, EDUCATION_CONTENT["en"])

    keyboard_buttons = []
    for topic_key_loop, topic_data_loop in topics.items():
        keyboard_buttons.append([InlineKeyboardButton(topic_data_loop["title"], callback_data=f"{TOPIC_CALLBACK}{lang_code}_{topic_key_loop}")])
    keyboard_buttons.append([InlineKeyboardButton("⬅️ Back to Languages", callback_data=BACK_TO_LANG_CALLBACK)])
    keyboard_buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data=MAIN_MENU_CALLBACK)])

    reply_markup = InlineKeyboardMarkup(keyboard_buttons)

    # If the previous message was a photo, this edit will fail.
    # We need to delete the photo and send a new text message.
    # For V1, we are simplifying image handling. If an image was last shown, this edit might look odd or fail.
    # A robust solution involves tracking message types or always sending new messages in complex nav.
    try:
        await query.edit_message_text(
            text=f"📚 Please choose a topic in {lang_code.upper()}:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.warning(f"Could not edit message on back_to_topics, likely due to media: {e}. Sending new message.")
        # Delete old message if possible, then send new one
        try: await query.message.delete()
        except: pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"📚 Please choose a topic in {lang_code.upper()}:",
            reply_markup=reply_markup
        )

async def handle_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles 'Main Menu' button press from within education module."""
    query = update.callback_query
    await query.answer()
    # Assuming get_main_menu_keyboard() is available (e.g. imported from onboarding or a general utils)
    # For now, let's just send a text and a fresh main menu keyboard.
    # A cleaner way would be to have a central main_menu command handler that can be called.
    from bot.handlers.onboarding import get_main_menu_keyboard as get_reply_main_menu

    await query.edit_message_text(text="Redirecting to main menu...") # Clear inline keyboard
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="🏠 You are back at the Main Menu.",
        reply_markup=get_reply_main_menu() # This sends the ReplyKeyboardMarkup
    )

# Handlers
education_command_handler = CommandHandler("learn", education_command)
education_button_handler = MessageHandler(Filters.Regex("^(📘 Learn About Ubuntium|Learn & Earn|Edukasi)$"), education_command)

# Callback Query Handlers for inline buttons
# Order matters: more specific regex first, or use specific callback data.
# Using specific callback data is more robust.
education_callback_handlers = [
    CallbackQueryHandler(handle_language_selection, pattern=f"^{LANG_CALLBACK}"),
    CallbackQueryHandler(handle_topic_selection, pattern=f"^{TOPIC_CALLBACK}"),
    CallbackQueryHandler(back_to_languages_handler, pattern=f"^{BACK_TO_LANG_CALLBACK}$"),
    CallbackQueryHandler(back_to_topics_handler, pattern=f"^{BACK_TO_TOPICS_CALLBACK}"),
    CallbackQueryHandler(handle_main_menu_callback, pattern=f"^{MAIN_MENU_CALLBACK}$")
]
