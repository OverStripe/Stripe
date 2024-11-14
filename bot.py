import os
import telebot
import requests
import re
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()
api_token = os.getenv('API_TOKEN')

# Check if the API token is loaded
if not api_token:
    logging.error("API_TOKEN is not set. Check your .env file.")
    exit("Bot token missing. Check .env file.")

bot = telebot.TeleBot(api_token)

# List of payment gateways
payment_gateways = [
    "paypal", "stripe", "braintree", "square", "cybersource", "authorize.net", "2checkout", "adyen",
    "worldpay", "sagepay", "checkout.com", "shopify", "razorpay", "bolt", "paytm", "venmo",
    "pay.google.com", "revolut", "eway", "woocommerce", "upi", "apple.com", "payflow", "payeezy",
    "paddle", "payoneer", "recurly", "klarna", "paysafe", "webmoney", "payeer", "payu", "skrill",
    "affirm", "afterpay", "dwolla", "global payments", "moneris", "nmi", "payment cloud",
    "paysimple", "paytrace", "stax", "alipay", "bluepay", "paymentcloud", "clover",
    "zelle", "google pay", "cashapp", "wechat pay", "transferwise", "stripe connect",
    "mollie", "sezzle", "afterpay", "payza", "gocardless", "bitpay", "sureship"
]

# Function to validate URLs
def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  
        r'localhost|'  
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  
        r'(?::\d+)?'  
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

# Detect payment gateways in response text
def find_payment_gateways(response_text):
    return [gateway.capitalize() for gateway in payment_gateways if gateway in response_text.lower()]

# Core function to check URL
def check_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        detected_gateways = find_payment_gateways(response.text)
        return detected_gateways, response.status_code

    except requests.exceptions.RequestException as e:
        return [f"Error: {str(e)}"], 500

# Start command with welcome message
@bot.message_handler(commands=['start'])
def cmd_start(message):
    welcome_message = (
        "➻ Welcome To Oᴠᴇʀ ❖ Sᴛʀɪᴘᴇ\n"
        "Incline Developer - [@TechPiro](https://t.me/TechPiro)\n"
        "Send a URL to check for payment gateways."
    )
    bot.send_message(message.chat.id, welcome_message, parse_mode="Markdown")

# Handler to process only messages with valid URLs
@bot.message_handler(func=lambda message: is_valid_url(message.text.strip()))
def handle_url(message):
    url = message.text.strip()
    detected_gateways, status_code = check_url(url)

    gateways_str = ', '.join(detected_gateways) if detected_gateways else "None"
    response_message = (
        f"🔍 Gateways Fetched Successfully ✅\n"
        f"━━━━━━━━━━━━━━\n"
        f"🔹 URL: {url}\n"
        f"🔹 Payment Gateways: {gateways_str}\n"
        f"🔹 Status Code: {status_code}\n"
        f"\nBot by [@TechPiro](https://t.me/TechPiro)"
    )
    
    bot.send_message(message.chat.id, response_message, parse_mode="Markdown")

# Infinite polling with error handling to keep the bot running
while True:
    try:
        bot.polling()
    except Exception as e:
        logging.error(f"Polling error: {e}")
        time.sleep(15)  # Wait before retrying polling
