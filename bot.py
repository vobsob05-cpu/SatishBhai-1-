import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import time

# --- 1. Configuration and Setup ---
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Placeholder for Master Password requirement
MASTER_PASSWORD = os.getenv("11115.8010164743", "secure123") 

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. Mock API Functions (Replace these with actual SDK calls) ---
def fetch_aadhaar_info(number):
    """Mock function to simulate UIDAI API call."""
    if number.startswith("91"):
        return {"name": "Ravi Sharma", "family_member_name": "Priya Sharma", "family_phone": "9876543210", "is_valid": True}
    return {"is_valid": False, "error": "Number not found in Aadhaar registry."}

def fetch_vehicle_info(number):
    """Mock function to simulate VAHAN API call."""
    if number.startswith("91"):
        return {"owner_name": "Anil Kumar", "vehicle_details": "DL 12 AB 1234"}
    return {"owner_name": "N/A", "vehicle_details": "Not found."}

def get_live_location(number):
    """Mock function for Geolocation API."""
    return {"latitude": 28.6139, "longitude": 77.2090, "city": "New Delhi, India"}

def analyze_chat_history(number):
    """Mock function for WhatsApp/Call Log API."""
    return {
        "calls": ["Vikram Singh (2023-10-01)", "Aisha Khan (2024-05-15)"],
        "chats": ["Priya Sharma (Last 50 messages)", "Work Group XYZ (Video Shared)"]
    }

def count_emails_by_number(number):
    """Mock function for Email API."""
    return {"email_count": 45, "platforms": ["Gmail", "Outlook"]}

# --- 3. Core Logic Functions ---

def authenticate_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handles initial password check."""
    global authenticated_users # Simple global to track login state
    if not hasattr(context, 'authenticated') or not context.authenticated:
        if update.message and update.message.text:
            # Assuming the user sends the password as the first command input
            entered_pass = update.message.text
            if entered_pass == MASTER_PASSWORD:
                context.authenticated = True
                logger.info(f"User successfully authenticated with password: {entered_pass}")
                return True
            else:
                update.message.reply_text("🔒 ACCESS DENIED. Please enter the correct password.")
                return False
        return False
    return True

async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles language selection post-authentication."""

    # Check if already set
    if hasattr(context.user_data, 'language') and context.user_data.language:
        await update.message.reply_text(f"✅ Language already set to {context.user_data.language.capitalize()}.")
        return

    keyboard = [
        [InlineKeyboardButton("🇮🇳 Hindi", callback_data='lang_hi')],
        [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🌐 Please select your preferred language:", 
        reply_markup=reply_markup
    )

async def process_number_intelligence(update: Update, context: ContextTypes.DEFAULT_TYPE, number: str, lang: str) -> str:
    """Runs all API calls for a single number and formats the output."""

    results = []

    # 1. Core Data Fetching
    aadhaar_data = fetch_aadhaar_info(number)
    vehicle_data = fetch_vehicle_info(number)
    location_data = get_live_location(number)
    chat_data = analyze_chat_history(number)
    email_count = count_emails_by_number(number)

    # 2. Formatting based on Language
    if lang == 'hi':
        # Hindi Output Formatting
        output = f"🌟 **{number} का विस्तृत विश्लेषण** 🌟\n\n"

        # Aadhaar Info
        output += "🆔 **आधार और परिवार जानकारी:**\n"
        if aadhaar_data.get("is_valid"):
            output += f"👤 नाम: {aadhaar_data['name']}\n"
            output += f"👨‍👩‍👧‍👦 परिवार सदस्य: {aadhaar_data['family_member_name']} ({aadhaar_data['family_phone']})\n"
        else:
            output += f"❌ आधार जानकारी उपलब्ध नहीं: {aadhaar_data.get('error', 'त्रुटि')}\n"

        # Vehicle Info
        output += "\n🚗 **वाहन जानकारी:**\n"
        output += f"🚗 विवरण: {vehicle_data['vehicle_details']} | मालिक का नाम: {vehicle_data['owner_name']}\n"

        # Location
        output += "\n📍 **लाइव लोकेशन:**\n"
        output += f"🌍 स्थान: {location_data.get('city', 'पता नहीं')} | अक्षांश/देशांतर: {location_data['latitude']}, {location_data['longitude']}\n"

        # Chat & Contact Info
        output += "\n💬 **संपर्क और चैट गतिविधि:**\n"
        output += f"📞 हालिया कॉल: {', '.join(chat_data['calls'])}\n"
        output += f"📸 चैट/वीडियो: {', '.join(chat_data['chats'])}\n"

        # Email Info
        output += "\n📧 **ईमेल सांख्यिकी:**\n"
        output += f"✉️ कुल अनुमानित ईमेल: {email_count['email_count']} ({', '.join(email_count['platforms'])})\n"

        return output

    else: # English Default
        output = f"🔎 **Detailed Analysis for Number: {number}** 🔎\n\n"

        # Aadhaar Info
        output += "🆔 **Aadhaar & Family Details:**\n"
        if aadhaar_data.get("is_valid"):
            output += f"👤 Name: {aadhaar_data['name']}\n"
            output += f"👨‍👩‍👧‍👦 Family Member: {aadhaar_data['family_member_name']} ({aadhaar_data['family_phone']})\n"
        else:
            output += f"❌ Aadhaar Data Unavailable: {aadhaar_data.get('error', 'Error')}\n"

        # Vehicle Info
        output += "\n🚗 **Vehicle Information:**\n"
        output += f"🚗 Details: {vehicle_data['vehicle_details']} | Owner Name: {vehicle_data['owner_name']}\n"

        # Location
        output += "\n📍 **Live Location:**\n"
        output += f"🌍 Location: {location_data.get('city', 'Unknown')} | Coordinates: {location_data['latitude']}, {location_data['longitude']}\n"

        # Chat & Contact Info
        output += "\n💬 **Contact & Chat Activity:**\n"
        output += f"📞 Recent Calls: {', '.join(chat_data['calls'])}\n"
        output += f"📸 Chats/Videos: {', '.join(chat_data['chats'])}\n"

        # Email Info
        output += "\n📧 **Email Statistics:**\n"
        output += f"✉️ Total Estimated Emails: {email_count['email_count']} ({', '.join(email_count['platforms'])})\n"

        return output


# --- 4. Telegram Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends welcome message and initiates the process."""
    await update.message.reply_text(
        f"👋 Hello! Welcome to DIG Number Intelligence System (DIG-ONE).\n"
        f"🔑 To start, please enter the MASTER PASSWORD: **{MASTER_PASSWORD}** (If not provided in .env)\n"
        f"🔑 Once authenticated, you can input a number to begin the analysis."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main handler for receiving text input (phone numbers or commands)."""

    if not context.authenticated:
        # If not authenticated, treat all input as potential password attempts
        await authenticate_user(update, context)
        return

    text = update.message.text.strip()

    # Check for command usage
    if text.lower() in ['start', '?']:
        await start_command(update, context)
        return

    # 1. Language selection prompt
    if not hasattr(context.user_data, 'language') or not context.user_data.language:
        await language_selection(update, context)
        return

    # 2. Process Input
    if text.isdigit() and len(text) >= 10: # Simple check for 10+ digit number
        phone_number = text
        lang = context.user_data.language

        await update.message.reply_text(f"🔍 Analyzing number {phone_number}...")

        # Run the intensive analysis function
        try:
            detailed_report = await process_number_intelligence(update, context, phone_number, lang)
            await update.message.reply_text(detailed_report, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error during analysis for {phone_number}: {e}")
            await update.message.reply_text(f"🚨 Analysis failed. Error: {e}. Please try another number.")
    else:
        await update.message.reply_text("❌ Invalid input. Please enter a valid Indian phone number (10+ digits) to begin analysis.")


# --- 5. Initialization ---
async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles Inline Keyboard clicks (Language Selection)."""
    query = update.callback_query
    await query.answer()

    if query.data == 'lang_hi':
        context.user_data['language'] = 'hi'
        await query.edit_message_text("✅ भाषा हिंदी (Hindi) के रूप में सेट हो गई है। अब नंबर दर्ज करें।")
    elif query.data == 'lang_en':
        context.user_data['language'] = 'en'
        await query.edit_message_text("✅ Language set to English. Enter a number to begin analysis.")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register Handlers
    application.add_handler(CommandHandler("start", start_command))

    # Primary message handler that checks authentication status
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Callback handler for inline keyboard clicks
    application.add_handler(CallbackQueryHandler(callback_query))

    logger.info("🚀 DIG Bot is starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()