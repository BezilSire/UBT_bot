import logging
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
from bot.utils.firebase_client import FirebaseClient
from bot.handlers.onboarding import get_main_menu_keyboard

logger = logging.getLogger(__name__)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Conversation states for vendor registration
(ASK_BUSINESS_NAME, ASK_LOCATION, ASK_CATEGORY,
 ASK_WALLET_ADDRESS, CONFIRM_DETAILS) = range(5)

# Conversation states for finding a vendor
FV_ASK_LOCATION, FV_ASK_CATEGORY, FV_SHOW_RESULTS = range(5, 8)  # Start range after vendor reg states


# --- Helper to format location for display ---
def format_location_display(location_data):
    if isinstance(location_data, dict):
        if location_data.get("type") == "gps":
            return f"GPS: Lat {location_data['latitude']:.4f}, Lon {location_data['longitude']:.4f}"
        return location_data.get("text", "Not provided")
    return str(location_data)


# --- Vendor Registration ---
async def register_vendor_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the vendor registration process."""
    user = update.effective_user
    logger.info(f"User {user.id} starting vendor registration.")

    # Initialize Firebase client if not already in bot_data
    if 'firebase_client' not in context.bot_data:
        try:
            context.bot_data['firebase_client'] = FirebaseClient()
        except Exception as e:
            logger.critical(f"FirebaseClient init failed in register_vendor_start: {e}")
            await update.message.reply_text("Service temporarily unavailable. Please try again later.", reply_markup=get_main_menu_keyboard())
            return ConversationHandler.END

    await update.message.reply_text(
        "Great! Let's register your business with Ubuntium. 🏪\n\n"
        "What is the name of your business?",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_BUSINESS_NAME

async def ask_business_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: # Renamed from receive_business_name for clarity
    """Receives business name and asks for location."""
    business_name = update.message.text.strip()
    if not (2 < len(business_name) < 100):
        await update.message.reply_text("Please enter a valid business name (3-99 characters).")
        return ASK_BUSINESS_NAME

    context.user_data['vendor_reg_name'] = business_name
    logger.info(f"User {update.effective_user.id} - Vendor Name: {business_name}")

    location_button = KeyboardButton(text="📍 Share My Location", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button], ["Or type your City/Region"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Thanks! Now, please share your business location. You can send your current location (tap below) or type the address/city.",
        reply_markup=keyboard
    )
    return ASK_LOCATION

async def ask_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: # Renamed
    """Receives location and asks for category."""
    user_location = None
    location_text_display = ""

    if update.message.location:
        user_location = {
            "latitude": update.message.location.latitude,
            "longitude": update.message.location.longitude,
            "type": "gps"
        }
        location_text_display = f"GPS ({user_location['latitude']:.2f}, {user_location['longitude']:.2f})"
    else:
        text_loc = update.message.text.strip()
        if not (2 < len(text_loc) < 100):
            await update.message.reply_text("Please enter a valid location description (3-99 characters).")
            return ASK_LOCATION
        user_location = {"text": text_loc, "type": "text"}
        location_text_display = text_loc

    context.user_data['vendor_reg_location'] = user_location
    logger.info(f"User {update.effective_user.id} - Vendor Location: {location_text_display}")

    categories = ["🛍️ Retail", "🍽️ Food & Drinks", "🚕 Transport", "📞 Airtime/Data", "🌾 Farming", "🛠️ Services", "🏠 Accommodation", "➕ Other"]
    # Create a 2-column layout for categories if many, or keep as single column list
    category_buttons = [[KeyboardButton(cat)] for cat in categories]
    # Example for 2 columns:
    # category_buttons = [categories[i:i + 2] for i in range(0, len(categories), 2)]

    await update.message.reply_text(
        "Got it! What category best describes your business? Please choose one from the list below.",
        reply_markup=ReplyKeyboardMarkup(category_buttons, one_time_keyboard=True, resize_keyboard=True)
    )
    return ASK_CATEGORY

async def ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: # Renamed
    """Receives category and asks for UBT wallet address."""
    category = update.message.text # Assuming category comes from button text
    # Basic validation if needed, but button selection is usually fine
    context.user_data['vendor_reg_category'] = category
    logger.info(f"User {update.effective_user.id} - Vendor Category: {category}")

    await update.message.reply_text(
        "Excellent. Now, please provide your UBT wallet address OR the phone number linked to your UBT account. "
        "This will be used for receiving payments.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_WALLET_ADDRESS

async def ask_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: # Renamed
    """Receives wallet address and asks for confirmation."""
    wallet_info = update.message.text.strip()
    # Basic validation (e.g., length, or specific format if UBT addresses have one)
    if not (5 < len(wallet_info) < 100): # Example validation
        await update.message.reply_text("Please enter a valid UBT wallet address or phone number (6-99 characters).")
        return ASK_WALLET_ADDRESS

    context.user_data['vendor_reg_wallet'] = wallet_info
    logger.info(f"User {update.effective_user.id} - Vendor Wallet: {wallet_info}")

    # Prepare confirmation message
    reg_name = context.user_data['vendor_reg_name']
    reg_location_data = context.user_data['vendor_reg_location']
    reg_category = context.user_data['vendor_reg_category']
    reg_wallet = context.user_data['vendor_reg_wallet']

    message = (
        "📝 *Please confirm your business details:*\n\n"
        f"🏢 *Business Name:* {reg_name}\n"
        f"📍 *Location:* {format_location_display(reg_location_data)}\n"
        f"🏷️ *Category:* {reg_category}\n"
        f"💳 *UBT Wallet/Phone:* {reg_wallet}\n\n"
        "Is all this information correct?"
    )
    keyboard = [[KeyboardButton("✅ Yes, Submit"), KeyboardButton("❌ No, Restart")]]
    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode='Markdown'
    )
    return CONFIRM_DETAILS

async def process_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes confirmation and saves vendor data."""
    user = update.effective_user
    user_id_str = str(user.id)

    if update.message.text == "✅ Yes, Submit":
        firebase_client: FirebaseClient = context.bot_data.get('firebase_client')
        if not firebase_client:
            logger.error(f"Firebase client not found in process_confirmation for user {user_id_str}")
            await update.message.reply_text("A critical error occurred. Please try /start again.", reply_markup=get_main_menu_keyboard())
            return ConversationHandler.END

        vendor_data = {
            "owner_telegram_id": user_id_str,
            "owner_telegram_username": user.username or "",
            "business_name": context.user_data['vendor_reg_name'],
            "location_data": context.user_data['vendor_reg_location'], # Stored as dict (gps) or text
            "category": context.user_data['vendor_reg_category'],
            "payment_info": context.user_data['vendor_reg_wallet'], # Wallet or phone
            "status": "pending_approval", # Or "approved" if no verification step needed initially
            "registered_at": datetime.utcnow().isoformat() + "Z", # UTC timestamp
            "telegram_user_details_at_registration": { # Snapshot of user details
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        }

        vendor_id = firebase_client.add_vendor(vendor_data)
        if vendor_id:
            logger.info(f"Vendor registration submitted by {user_id_str} (UserB): {vendor_id} - {vendor_data['business_name']}")

            # 1. Update UserB's record to set vendor_registered = true
            firebase_client.update_user_field(user_id_str, "vendor_registered", True)
            logger.info(f"Set vendor_registered=true for user {user_id_str}")

            # 2. Check if UserB was referred and reward their referrer (UserA)
            user_b_data = firebase_client.get_user(user_id_str) # Get UserB's full data
            if user_b_data and user_b_data.get("referred_by_code"):
                referrer_code = user_b_data["referred_by_code"]
                user_a_data = firebase_client.find_user_by_referral_code(referrer_code)

                if user_a_data and user_a_data.get("telegram_id"):
                    user_a_id = str(user_a_data.get("telegram_id"))
                    vendor_reg_bonus = 3 # +3 UBT for vendor registration

                    if firebase_client.add_referral_reward(user_a_id, vendor_reg_bonus):
                        logger.info(f"Awarded +{vendor_reg_bonus} UBT to referrer {user_a_id} because their referral {user_id_str} registered as a vendor.")
                        try:
                            user_b_name = user_b_data.get("name", "Your referral")
                            await context.bot.send_message(
                                chat_id=user_a_id,
                                text=f"🎉 {user_b_name} (whom you referred) just registered as a vendor! You've earned +{vendor_reg_bonus} UBT."
                            )
                        except Exception as e:
                            logger.error(f"Failed to send vendor registration bonus notification to referrer {user_a_id}: {e}")
                    else:
                        logger.error(f"Failed to add vendor registration bonus for referrer {user_a_id}.")
                else:
                    logger.warning(f"Referrer with code {referrer_code} (for vendor {user_id_str}) not found.")
            else:
                logger.info(f"User {user_id_str} (vendor) was not referred or their data is incomplete. No vendor registration bonus for referrer.")

            await update.message.reply_text(
                "🎉 Your business registration has been submitted successfully!\n"
                "We'll review it and notify you once it's approved. "
                "Thank you for joining the Ubuntium merchant network!",
                reply_markup=get_main_menu_keyboard()
            )

            # Notify admin
            if ADMIN_CHAT_ID:
                try:
                    admin_message = (
                        f"🔔 *New Vendor Registration for Ubuntium Bot* 🔔\n\n"
                        f"🏢 *Business Name:* {vendor_data['business_name']}\n"
                        f"👤 *Submitted by:* {user.full_name} (@{user.username}, ID: {user_id_str})\n"
                        f"📍 *Location:* {format_location_display(vendor_data['location_data'])}\n"
                        f"🏷️ *Category:* {vendor_data['category']}\n"
                        f"💳 *Payment Info:* {vendor_data['payment_info']}\n"
                        f"🕒 *Submitted At:* {vendor_data['registered_at']}\n\n"
                        f"Vendor ID (Firestore): {vendor_id}"
                    )
                    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Failed to send vendor registration notification to admin {ADMIN_CHAT_ID}: {e}")
            else:
                logger.warning("ADMIN_CHAT_ID not set. Cannot send vendor registration notification.")
        else:
            logger.error(f"Failed to save vendor registration for user {user_id_str} to Firebase.")
            await update.message.reply_text(
                "Sorry, there was an issue submitting your registration. Please try again.",
                reply_markup=get_main_menu_keyboard()
            )
    else: # Chose "No, Restart"
        await update.message.reply_text(
            "No problem. Let's start the registration over.\n\nWhat is the name of your business?",
            reply_markup=ReplyKeyboardRemove()
        )
        # Clear only vendor registration specific data
        for key in ['vendor_reg_name', 'vendor_reg_location', 'vendor_reg_category', 'vendor_reg_wallet']:
            context.user_data.pop(key, None)
        return ASK_BUSINESS_NAME # Restart the flow from the beginning

    # Clear vendor registration data from context after successful submission or full restart
    for key in ['vendor_reg_name', 'vendor_reg_location', 'vendor_reg_category', 'vendor_reg_wallet']:
        context.user_data.pop(key, None)
    return ConversationHandler.END

async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the vendor registration process."""
    logger.info(f"User {update.effective_user.id} cancelled vendor registration.")
    await update.message.reply_text(
        "Vendor registration cancelled. You can start again anytime from the main menu.",
        reply_markup=get_main_menu_keyboard()
    )
    for key in ['vendor_reg_name', 'vendor_reg_location', 'vendor_reg_category', 'vendor_reg_wallet']:
        context.user_data.pop(key, None)
    return ConversationHandler.END

# --- Find Vendor Flow ---
async def find_vendor_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the find vendor process by asking for location."""
    user = update.effective_user
    logger.info(f"User {user.id} starting 'Find Vendor' flow.")
    # Ensure Firebase client is available
    if 'firebase_client' not in context.bot_data:
        try:
            context.bot_data['firebase_client'] = FirebaseClient()
        except Exception as e:
            logger.critical(f"FirebaseClient init failed in find_vendor_start: {e}")
            await update.message.reply_text("Service temporarily unavailable. Please try again later.", reply_markup=get_main_menu_keyboard())
            return ConversationHandler.END

    location_button = KeyboardButton(text="📍 Use My Current Location", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button], ["Or type your City/Area"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Let's find a UBT vendor near you! 🗺️\n\n"
        "Please share your current location (tap button below) or type the name of your city/area.",
        reply_markup=keyboard
    )
    return FV_ASK_LOCATION

async def fv_receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives location, then asks for category (optional) or shows results."""
    user = update.effective_user
    search_location_input = None
    display_location_text = ""

    if update.message.location:
        search_location_input = {
            "latitude": update.message.location.latitude,
            "longitude": update.message.location.longitude,
            "type": "gps"
        }
        display_location_text = f"your current GPS location"
        logger.info(f"User {user.id} provided GPS location for vendor search: {search_location_input}")
    else:
        text_input = update.message.text.strip()
        if not (2 < len(text_input) < 50):
            await update.message.reply_text("Please enter a valid city or area name (3-49 characters).")
            # Re-ask for location
            location_button = KeyboardButton(text="📍 Use My Current Location", request_location=True)
            keyboard = ReplyKeyboardMarkup([[location_button], ["Or type your City/Area"]], resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Please try again:", reply_markup=keyboard)
            return FV_ASK_LOCATION
        search_location_input = text_input # Store the raw text input
        display_location_text = search_location_input
        logger.info(f"User {user.id} provided text location for vendor search: {search_location_input}")

    context.user_data['find_vendor_location_query'] = search_location_input

    # For this iteration, we will skip asking for category and directly show results.
    # To add category filtering later, change this to return FV_ASK_CATEGORY
    # and implement fv_ask_category and fv_receive_category methods.

    firebase_client: FirebaseClient = context.bot_data['firebase_client']

    # The find_vendors method in firebase_client was updated to handle text search better.
    # If search_location_input is GPS, find_vendors will currently return all approved.
    vendors = firebase_client.find_vendors(location_query=search_location_input, category_query=None)

    if vendors:
        response_message = f"🔎 Found these UBT vendors based on location: *{display_location_text}*\n\n"
        if isinstance(search_location_input, dict) and search_location_input.get("type") == "gps":
             response_message += "(Note: Precise distance filtering for GPS is under development. Showing all approved vendors for now.)\n\n"

        for vendor in vendors[:10]: # Limit to 10 results for now to avoid message overload
            response_message += f"🏪 *{vendor.get('business_name', 'N/A')}*\n"
            response_message += f"🏷️ Category: {vendor.get('category', 'N/A')}\n"
            # Display text location if available, otherwise a generic message
            loc_data = vendor.get('location_data', {})
            vendor_loc_display = format_location_display(loc_data)
            response_message += f"📍 Location: {vendor_loc_display}\n"
            # Placeholder for contact/directions
            # response_message += f"📞 Contact: {vendor.get('payment_info', 'N/A')}\n" # Assuming payment_info might be phone
            response_message += "--------------------\n"

        if len(vendors) > 10:
            response_message += f"\nShowing first 10 of {len(vendors)} vendors."

        await update.message.reply_text(response_message, parse_mode='Markdown', reply_markup=get_main_menu_keyboard())
    else:
        no_vendor_message = f"😔 Sorry, I couldn't find any UBT vendors matching your criteria for *{display_location_text}* at the moment.\n"
        if isinstance(search_location_input, dict) and search_location_input.get("type") == "gps":
             no_vendor_message += "(Note: Precise distance filtering for GPS is under development.)\n"
        no_vendor_message += "More vendors are joining daily, so please check back soon or try a different area!"
        await update.message.reply_text(no_vendor_message, parse_mode='Markdown', reply_markup=get_main_menu_keyboard())

    context.user_data.pop('find_vendor_location_query', None)
    return ConversationHandler.END

async def fv_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the find vendor process."""
    logger.info(f"User {update.effective_user.id} cancelled 'Find Vendor' flow.")
    context.user_data.pop('find_vendor_location_query', None)
    context.user_data.pop('find_vendor_category_query', None) # If category step was added
    await update.message.reply_text(
        "Vendor search cancelled. Returning to the main menu.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


# Handlers
register_vendor_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^(💼 Register My Business|Register Vendor)$"), register_vendor_start),
        CommandHandler("registervendor", register_vendor_start)
    ],
    states={
        ASK_BUSINESS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_business_name)],
        ASK_LOCATION: [MessageHandler(filters.LOCATION | (filters.TEXT & ~filters.COMMAND), ask_location)],
        ASK_CATEGORY: [MessageHandler(filters.Regex("^(🛍️ Retail|🍽️ Food & Drinks|🚕 Transport|📞 Airtime/Data|🌾 Farming|🛠️ Services|🏠 Accommodation|➕ Other)$"), ask_category)],
        ASK_WALLET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_wallet_address)],
        CONFIRM_DETAILS: [MessageHandler(filters.Regex("^(✅ Yes, Submit|❌ No, Restart)$"), process_confirmation)],
    },
    fallbacks=[CommandHandler("cancel", cancel_registration), MessageHandler(filters.Regex("^(Cancel|Stop)$"), cancel_registration)],
    # persistent=True, name="vendor_registration_conversation" # For persistence
)

find_vendor_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(r"^(📍 Find a UBT Vendor|Find Vendor)$"), find_vendor_start),
        CommandHandler("findvendor", find_vendor_start)
    ],
    states={
        FV_ASK_LOCATION: [MessageHandler(filters.LOCATION | (filters.TEXT & ~filters.COMMAND), fv_receive_location)],
        # FV_ASK_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, fv_receive_category)], # If category step is added
    },
    fallbacks=[
        CommandHandler("cancel", fv_cancel),
        MessageHandler(filters.Regex("^(Cancel|Stop)$"), fv_cancel)
    ],
    # persistent=True, name="find_vendor_conversation" # For persistence
)
