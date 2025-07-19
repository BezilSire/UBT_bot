import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from bot.utils.firebase_client import FirebaseClient

logger = logging.getLogger(__name__)

async def my_referrals_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /myreferrals command and 'My Referrals' / 'Invite Friends' button."""
    user = update.effective_user
    user_id_str = str(user.id)

    if 'firebase_client' not in context.bot_data:
        logger.error("Firebase client not available in my_referrals_command.")
        # Attempt to initialize it, as it might be the first interaction after a restart
        try:
            context.bot_data['firebase_client'] = FirebaseClient()
            logger.info("FirebaseClient re-initialized in referral handler.")
        except Exception as e:
            logger.critical(f"Failed to initialize FirebaseClient in referral handler: {e}", exc_info=True)
            await update.message.reply_text("Sorry, there's a problem fetching your referral data. Please try again later.")
            return

    firebase_client: FirebaseClient = context.bot_data['firebase_client']
    db_user = firebase_client.get_user(user_id_str)

    if not db_user:
        logger.warning(f"User {user_id_str} not found in Firebase for referrals command.")
        await update.message.reply_text(
            "I couldn't find your details. Have you completed the /start setup?"
        )
        return

    num_referrals = db_user.get('referral_count', 0)
    rewards_earned = db_user.get('referral_rewards_balance', 0.0) # Ensure this field name is consistent
    referral_code = db_user.get('referral_code')

    if not referral_code:
        # This case should ideally not happen if onboarding is complete
        logger.error(f"User {user_id_str} has no referral_code in Firebase despite being fetched.")
        # Potentially generate one here if absolutely necessary and save it, but it's a sign of an issue.
        # For now, inform the user.
        await update.message.reply_text(
            "Sorry, I couldn't find your unique referral code. Please contact support or try /start again."
        )
        return

    bot_username = context.bot.username
    # The referral link should use the user's actual referral_code from DB
    referral_link = f"https://t.me/{bot_username}?start=ref_{referral_code}"

    message_text = (
        f"🌟 Your Referral Stats 🌟\n\n"
        f"🙋‍♂️ Friends Invited: {num_referrals}\n"
        f"💰 UBT Rewards Earned: {rewards_earned:.2f} UBT\n\n" # Format to 2 decimal places
        f"🔗 Your Unique Referral Link:\n`{referral_link}`\n\n"
        f"Share this link with your friends to invite them to Ubuntium and earn rewards!"
    )

    # Prepare a message to be shared, including the referral link
    share_message_text = (
        f"Join me on Ubuntium, Africa's financial revolution! 🌍💰\n"
        f"Sign up using my link and let's grow together: {referral_link}"
    )

    keyboard = [
        [InlineKeyboardButton("🔗 Share My Link Now!", switch_inline_query=share_message_text)],
        # [InlineKeyboardButton("🏆 Top Referrers", callback_data="ref_leaderboard")] # Optional: for leaderboard
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

# `invite_friends_button` is effectively covered by the regex in `invite_friends_handler`
# which calls `my_referrals_command`. No separate function needed unless different behavior is desired.

# Handlers to be imported by main.py
my_referrals_handler = CommandHandler("myreferrals", my_referrals_command)
# Catches "My Referrals", "Invite Friends", or "🎁 My Referrals" (emoji from main menu)
# It's good practice to match the exact button text if possible.
invite_friends_handler = MessageHandler(
    filters.Regex(r"^(\🎁 My Referrals|Invite Friends|My Referrals|Referral)$"),
    my_referrals_command
)
