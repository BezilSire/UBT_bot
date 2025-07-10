import logging
import re # For phone number validation
import uuid # For generating unique referral codes
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, Filters, ConversationHandler
from bot.utils.firebase_client import FirebaseClient # Assuming FirebaseClient is set up
from . import education # Import education module to access its commands/handlers
from datetime import datetime

# Basic logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states for onboarding
NAME, PHONE, LOCATION, ASK_BASE_WALLET, ONBOARDING_COMPLETE = range(5)

# Main menu keyboard (could be moved to a shared utils module)
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        # [KeyboardButton("🚀 Get Started"), KeyboardButton("🔐 Already Have Wallet")], # Get Started removed after onboarding
        [KeyboardButton("💳 Check My Wallet"), KeyboardButton("🎁 My Referrals")],
        [KeyboardButton("📍 Find a UBT Vendor"), KeyboardButton("💼 Register My Business")],
        [KeyboardButton("📘 Learn About Ubuntium"), KeyboardButton("🆘 Help")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Sends a welcome message and main options.
    Checks if user exists. If so, shows main menu. If not, can direct to onboarding.
    Also handles referral links.
    """
    user = update.effective_user
    user_id_str = str(user.id)
    logger.info(f"User {user_id_str} ({user.username}) started the bot. Args: {context.args}")

    # Initialize Firebase client if not already in bot_data
    if 'firebase_client' not in context.bot_data:
        try:
            context.bot_data['firebase_client'] = FirebaseClient()
            logger.info("FirebaseClient initialized and added to bot_data.")
        except Exception as e:
            logger.critical(f"Failed to initialize FirebaseClient in start handler: {e}", exc_info=True)
            await update.message.reply_text("Sorry, there's a problem connecting to our services. Please try again later.")
            return ConversationHandler.END

    firebase_client: FirebaseClient = context.bot_data['firebase_client']

    # Check for referral codes
    referred_by_id = None
    if context.args:
        try:
            payload = context.args[0]
            if payload.startswith("ref_"):
                referred_by_id = payload.split("ref_")[1]
                # Validate if referrer_id is a valid user ID (optional, depends on how codes are generated)
                logger.info(f"User {user_id_str} was referred by referral code: {referred_by_id}")
                # Store it in user_data to process after onboarding
                context.user_data['referred_by_code'] = referred_by_id
        except Exception as e:
            logger.error(f"Error processing referral payload '{context.args[0]}': {e}")

    # Check if user already exists in Firebase
    db_user = firebase_client.get_user(user_id_str)
    if db_user and db_user.get('onboarding_completed'):
        welcome_message = f"Welcome back, {db_user.get('name', user.first_name)}!\nWhat would you like to do today?"
        await update.message.reply_text(welcome_message, reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END # User already onboarded

    # New user or incomplete onboarding
    if referred_by_id:
        await update.message.reply_text(
            f"Welcome to Ubuntium! It looks like you were invited. Let's get you set up."
        )

    reply_keyboard = [
        [KeyboardButton("🚀 Get Started")],
        [KeyboardButton("📘 Learn About Ubuntium")],
        [KeyboardButton("🆘 Help")] # Already Have Wallet might be complex if they started with /start
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)

    welcome_text = (
        "Welcome to Ubuntium — Africa’s financial revolution! 🌍💰\n\n"
        "I'm your Ubuntium Assistant. To begin, let's get you started or you can learn more about us."
    )
    await update.message.reply_text(welcome_text, reply_markup=markup)
    return ConversationHandler.END # Let them choose Get Started to enter the flow

async def start_onboarding_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the actual onboarding data collection after user clicks 'Get Started'."""
    logger.info(f"User {update.effective_user.id} initiated onboarding flow.")
    await update.message.reply_text(
        "Great! Let's get you set up in the Ubuntium network. This will only take a moment.\n\n"
        "First, what should I call you? (Please enter your full name)",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves name and asks for phone number."""
    user_name = update.message.text.strip()
    if len(user_name) < 2 or len(user_name) > 50: # Basic validation
        await update.message.reply_text("Hmm, that name seems a bit off. Please enter a valid name (2-50 characters).")
        return NAME

    context.user_data['onboarding_name'] = user_name
    logger.info(f"User {update.effective_user.id} provided name: {user_name}")

    phone_button = KeyboardButton(text="📱 Share My Phone Number", request_contact=True)
    manual_phone_keyboard = ReplyKeyboardMarkup([[phone_button], ["Or type your phone number (e.g., +254... YY)"]], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"Thanks, {user_name}! Now, could you share your phone number? "
        "This helps us secure your account and connect you with the community.\n\n"
        "You can tap the button below or type it in (including country code, e.g., +254xxxxxxxxx).",
        reply_markup=manual_phone_keyboard
    )
    return PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves phone number (from contact or text) and asks for location."""
    user = update.effective_user
    phone_number = None

    if update.message.contact:
        phone_number = update.message.contact.phone_number
        logger.info(f"User {user.id} shared contact: {phone_number}")
    else:
        text_phone = update.message.text.strip()
        # Basic validation for international phone numbers (starts with +, then digits)
        if re.match(r"^\+?[0-9\s-]{7,15}$", text_phone):
            phone_number = text_phone
            if not phone_number.startswith('+'): # Add + if missing and looks like a phone number
                # This is a heuristic, might need better country code handling
                # For now, assumes user might forget '+' but includes country code digits
                phone_number = f"+{phone_number}"
            logger.info(f"User {user.id} typed phone: {phone_number}")
        else:
            await update.message.reply_text(
                "That doesn't look like a valid phone number. Please try again, including your country code (e.g., +254xxxxxxxxx)."
            )
            return PHONE

    context.user_data['onboarding_phone'] = phone_number

    location_button = KeyboardButton(text="📍 Share My Location", request_location=True)
    manual_location_keyboard = ReplyKeyboardMarkup([[location_button], ["Or type your City/Region"]], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Got it! Lastly, where are you primarily based? "
        "This helps us connect you with local vendors and opportunities.\n\n"
        "Share your current location, or type your city/region.",
        reply_markup=manual_location_keyboard
    )
    return LOCATION

async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves location and asks for Base wallet address."""
    user = update.effective_user
    # user_id_str = str(user.id) # Not needed here anymore, will be in receive_base_wallet
    location_data = None

    if update.message.location:
        location_data = {
            "latitude": update.message.location.latitude,
            "longitude": update.message.location.longitude,
            "type": "gps"
        }
        logger.info(f"User {user.id} shared GPS location: {location_data}")
    else:
        text_location = update.message.text.strip()
        if len(text_location) < 2 or len(text_location) > 50:
            await update.message.reply_text("Please enter a valid city or region name (2-50 characters).")
            return LOCATION
        location_data = {"text": text_location, "type": "text"}
        logger.info(f"User {user.id} typed location: {text_location}")

    context.user_data['onboarding_location'] = location_data

    # --- All data collected, save to Firebase ---
    if 'firebase_client' not in context.bot_data:
        logger.error("Firebase client not found in bot_data during receive_location. Critical.")
        await update.message.reply_text("A critical error occurred. Please try /start again.", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    firebase_client: FirebaseClient = context.bot_data['firebase_client']

    # Generate a unique referral code for the new user
    # Using first part of UUID for simplicity, ensure it's unique enough or check for collisions
    unique_ref_code = f"UBT{str(uuid.uuid4())[:8].upper()}"
    context.user_data['referral_code'] = unique_ref_code

    user_payload = {
        "telegram_id": user_id_str,
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "name": context.user_data['onboarding_name'],
        "phone_number": context.user_data['onboarding_phone'],
        "location": context.user_data['onboarding_location'],
        "referral_code": unique_ref_code,
        "referred_by_code": context.user_data.get('referred_by_code'), # Store who referred them
        "created_at": datetime.utcnow().isoformat() + "Z",
        "onboarding_completed": True,
        "ubt_balance": 0.0, # Initial balance
        "referral_rewards_balance": 0.0,
        "referral_count": 0
    }

    if firebase_client.create_user(user_id_str, user_payload):
        logger.info(f"User {user_id_str} successfully onboarded and data saved to Firebase.")

        # Handle referral if applicable
        referred_by_code = context.user_data.get('referred_by_code')
        if referred_by_code:
            # Find the referrer user by their referral_code
            # This requires a query on the 'users' collection where 'referral_code' == referred_by_code
            # For now, let's assume firebase_client has a method like find_user_by_referral_code(code)
            # And then increment their count and give reward.
            # This part needs a robust implementation in firebase_client.py
            # Example:
            # referrer = firebase_client.find_user_by_referral_code(referred_by_code)
            # if referrer:
            #     firebase_client.increment_referral_count(referrer['telegram_id'])
            #     firebase_client.add_referral_reward(referrer['telegram_id'], 10) # Example 10 UBT reward
            #     logger.info(f"Processed referral for {user_id_str} by {referred_by_code} (referrer ID: {referrer['telegram_id']})")
            #     await context.bot.send_message(chat_id=referrer['telegram_id'], text=f"🎉 Someone you referred ({user_payload['name']}) just joined Ubuntium! You've earned a reward.")
            # else:
            #     logger.warning(f"Referrer with code {referred_by_code} not found.")
            # pass # Placeholder for actual referral processing logic
            # Actual referral processing:
            if referred_by_code:
                referrer_user = firebase_client.find_user_by_referral_code(referred_by_code)
                if referrer_user and referrer_user.get('telegram_id'):
                    referrer_telegram_id = referrer_user['telegram_id']
                    # Ensure not referring oneself (though code uniqueness should prevent this if properly assigned)
                    if referrer_telegram_id != user_id_str:
                        reward_amount = 10 # Example: 10 UBT reward
                        if firebase_client.increment_referral_count(referrer_telegram_id) and \
                           firebase_client.add_referral_reward(referrer_telegram_id, reward_amount):
                            logger.info(f"Successfully processed referral for new user {user_id_str} by referrer {referrer_telegram_id} (code: {referred_by_code}).")
                            try:
                                await context.bot.send_message(
                                    chat_id=referrer_telegram_id,
                                    text=f"🎉 Someone you referred ({user_payload['name']}) just joined Ubuntium! You've earned {reward_amount} UBT."
                                )
                            except Exception as e:
                                logger.error(f"Failed to send referral notification to {referrer_telegram_id}: {e}")
                        else:
                            logger.error(f"Failed to update count/reward for referrer {referrer_telegram_id}.")
                    else:
                        logger.info(f"User {user_id_str} attempted to refer themselves with code {referred_by_code}. No action taken.")
                else:
                    logger.warning(f"Referrer with code {referred_by_code} not found or has no telegram_id.")


        await update.message.reply_text(
            f"🎉 Welcome aboard, {context.user_data['onboarding_name']}! You are now part of the Ubuntium family.\n\n"
            f"Your unique referral code is: `{unique_ref_code}` (Share this to earn rewards!)\n\n"
            "You can now explore the main menu.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    else:
        logger.error(f"Failed to save user {user_id_str} to Firebase.")
        await update.message.reply_text(
            "Sorry, there was an issue saving your details. Please try /start again.",
            reply_markup=get_main_menu_keyboard() # Or back to start options
        )

    context.user_data['onboarding_location'] = location_data

    # Now ask for Base wallet address
    await update.message.reply_text(
        "Thanks! One last important step.\n\n"
        "Please provide your **Base network wallet address** (from a non-custodial wallet like MetaMask, Trust Wallet, Coinbase Wallet, etc.). "
        "This is where your earned UBT rewards will be sent monthly.\n\n"
        "It should start with `0x` and be 42 characters long. Please double-check it for accuracy!",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_BASE_WALLET

async def receive_base_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves Base wallet address and completes onboarding."""
    user = update.effective_user
    user_id_str = str(user.id)
    base_wallet_address = update.message.text.strip()

    # Basic validation for Base address (starts with 0x, 42 chars)
    if not re.match(r"^0x[a-fA-F0-9]{40}$", base_wallet_address):
        await update.message.reply_text(
            "Hmm, that doesn't look like a valid Base wallet address. "
            "It should start with `0x` and be 42 characters long (e.g., `0x123...abc`).\n\nPlease try again.",
            parse_mode='Markdown'
        )
        return ASK_BASE_WALLET

    context.user_data['onboarding_base_payout_address'] = base_wallet_address
    logger.info(f"User {user_id_str} provided Base wallet: {base_wallet_address}")

    # --- All data collected, save to Firebase ---
    if 'firebase_client' not in context.bot_data:
        logger.error("Firebase client not found in bot_data during receive_base_wallet. Critical.")
        await update.message.reply_text("A critical error occurred. Please try /start again.", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    firebase_client: FirebaseClient = context.bot_data['firebase_client']

    unique_ref_code = context.user_data.get('referral_code') # Should have been set if this is a new user
    if not unique_ref_code: # Should ideally not happen if logic is correct
        unique_ref_code = f"UBT{str(uuid.uuid4())[:8].upper()}"
        context.user_data['referral_code'] = unique_ref_code
        logger.warning(f"Referral code was missing for user {user_id_str}, generated a new one: {unique_ref_code}")


    user_payload = {
        "telegram_id": user_id_str,
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "name": context.user_data['onboarding_name'],
        "phone_number": context.user_data['onboarding_phone'],
        "location": context.user_data['onboarding_location'], # This is the dict
        "base_payout_address": context.user_data['onboarding_base_payout_address'],
        "referral_code": unique_ref_code,
        "referred_by_code": context.user_data.get('referred_by_code'),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "onboarding_completed": True,
        "ubt_balance": 0.0,
        "referral_rewards_balance": 0.0, # Still useful for tracking source of funds if needed
        "referral_count": 0
    }

    if firebase_client.create_user(user_id_str, user_payload):
        logger.info(f"User {user_id_str} successfully onboarded with Base wallet and data saved.")

        referred_by_code = context.user_data.get('referred_by_code')
        if referred_by_code:
            referrer_user = firebase_client.find_user_by_referral_code(referred_by_code)
            if referrer_user and referrer_user.get('telegram_id'):
                referrer_telegram_id = referrer_user['telegram_id']
                if referrer_telegram_id != user_id_str:
                    reward_amount = 10
                    if firebase_client.increment_referral_count(referrer_telegram_id) and \
                       firebase_client.add_referral_reward(referrer_telegram_id, reward_amount):
                        logger.info(f"Processed referral for {user_id_str} by {referrer_telegram_id}.")
                        try:
                            await context.bot.send_message(
                                chat_id=referrer_telegram_id,
                                text=f"🎉 Someone you referred ({user_payload['name']}) just joined Ubuntium! You've earned {reward_amount} UBT (this will be added to your monthly payout)."
                            )
                        except Exception as e:
                            logger.error(f"Failed to send referral notification to {referrer_telegram_id}: {e}")
                    else:
                        logger.error(f"Failed to update count/reward for referrer {referrer_telegram_id}.")
                else:
                    logger.warning(f"Referrer with code {referred_by_code} not found.")

        success_message = (
            f"🎉 Welcome aboard, {context.user_data['onboarding_name']}! You are now part of the Ubuntium family.\n\n"
            f"Your Base payout address is set to: `{base_wallet_address}`\n"
            f"Your unique referral code is: `{unique_ref_code}` (Share this to earn UBT!)\n\n"
            "All UBT you earn will be tracked here and paid out to your Base address monthly. "
            "You can now explore the main menu."
        )
        await update.message.reply_text(success_message, reply_markup=get_main_menu_keyboard(), parse_mode='Markdown')
    else:
        logger.error(f"Failed to save user {user_id_str} to Firebase.")
        await update.message.reply_text(
            "Sorry, there was an issue saving your details. Please try /start again.",
            reply_markup=get_main_menu_keyboard()
        )

    # Clean up all onboarding data from context.user_data
    for key in ['onboarding_name', 'onboarding_phone', 'onboarding_location', 'onboarding_base_payout_address', 'referred_by_code', 'referral_code']:
        context.user_data.pop(key, None)

    return ConversationHandler.END


async def handle_already_have_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'Already Have Wallet' button press."""
    # This flow is not fully part of the onboarding ConversationHandler here,
    # but could be its own conversation or a simple message for now.
    user_id_str = str(update.effective_user.id)
    if 'firebase_client' not in context.bot_data: # Ensure client is available
        try:
            context.bot_data['firebase_client'] = FirebaseClient()
        except Exception as e:
            logger.critical(f"FirebaseClient init failed in handle_already_have_wallet: {e}")
            await update.message.reply_text("Service temporarily unavailable. Please try again later.")
            return ConversationHandler.END # Or appropriate state if in a convo

    firebase_client: FirebaseClient = context.bot_data['firebase_client']
    db_user = firebase_client.get_user(user_id_str)

    if db_user and db_user.get('onboarding_completed'):
        await update.message.reply_text(
            f"Welcome back, {db_user.get('name', update.effective_user.first_name)}! You're already set up.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # User might have clicked this but isn't in DB or onboarding not complete
        await update.message.reply_text(
            "It seems you haven't completed the initial setup yet. "
            "Please click '🚀 Get Started' to join Ubuntium!",
            # Provide a keyboard that leads to 'Get Started'
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🚀 Get Started")]], resize_keyboard=True, one_time_keyboard=True)
        )
    return ConversationHandler.END # Not part of the main onboarding sequence states


async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the onboarding process."""
    logger.info(f"User {update.effective_user.id} cancelled onboarding.")
    # Clean up any partial data
    for key in ['onboarding_name', 'onboarding_phone', 'onboarding_location', 'referred_by_code']:
        context.user_data.pop(key, None)

    await update.message.reply_text(
        "Onboarding cancelled. You can always /start again when you're ready!",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🚀 Get Started"), KeyboardButton("📘 Learn About Ubuntium")]], resize_keyboard=True)
    )
    return ConversationHandler.END

# Define handlers to be imported by main.py
start_handler = CommandHandler("start", start) # This now acts as an entry point resolver

# Onboarding ConversationHandler
onboarding_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.Regex("^🚀 Get Started$"), start_onboarding_flow)],
    states={
        NAME: [MessageHandler(Filters.TEXT & ~Filters.COMMAND, receive_name)],
        PHONE: [MessageHandler(Filters.CONTACT | (Filters.TEXT & ~Filters.COMMAND), receive_phone)],
        LOCATION: [MessageHandler(Filters.LOCATION | (Filters.TEXT & ~Filters.COMMAND), receive_location)],
        ASK_BASE_WALLET: [MessageHandler(Filters.TEXT & ~Filters.COMMAND, receive_base_wallet)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_onboarding),
        MessageHandler(Filters.Regex("^(Cancel|Stop)$"), cancel_onboarding)
    ],
    # per_user=True, per_chat=True # Default behavior, good for user-specific flows
    # persistent=True, name="onboarding_conversation" # For persistence across bot restarts if PicklePersistence is used
)

# Other handlers that are not part of the conversation but might be on the initial screen
already_have_wallet_handler = MessageHandler(Filters.Regex("^🔐 Already Have Wallet$"), handle_already_have_wallet)
# Learn About Ubuntium and Help are handled by their respective modules.
learn_about_handler = MessageHandler(Filters.Regex("^📘 Learn About Ubuntium$"), education.education_command) # Direct to education module
# This should be defined in education.py and imported, temp placeholder:
# async def temp_edu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("Education module selected (linking properly soon).")
# learn_about_handler = MessageHandler(Filters.Regex("^📘 Learn About Ubuntium$"), temp_edu_start)
