import os
import telebot
import requests
import re
from dotenv import load_dotenv

# Load environment variables from .env file for secure API token management
load_dotenv()
api_token = os.getenv('API_TOKEN')
bot = telebot.TeleBot(api_token)

# Expanded list of payment gateways
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

# Bot usage statistics
bot_stats = {
    "total_checks": 0,
    "unique_urls": set(),
}

# Validate URL format
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
    detected_gateways = [gateway.capitalize() for gateway in payment_gateways if gateway in response_text.lower()]
    return detected_gateways

# Check for various security features
def check_captcha(response_text):
    captcha_keywords = ['captcha', 'robot', 'verification', 'prove you are not a robot', 'challenge']
    return any(keyword in response_text.lower() for keyword in captcha_keywords)

def check_cloudflare(response_text):
    cloudflare_keywords = ['cf-', 'cloudflare', 'access denied', 'please wait', 'checking your browser']
    return any(keyword in response_text.lower() for keyword in cloudflare_keywords)

def check_3d_secure(response_text):
    secure_keywords = [
        "3dsecure", "3d secure", "secure3d", "secure checkout", "verified by visa",
        "mastercard securecode", "secure verification", "3d-authentication", "3d-auth"
    ]
    return any(keyword in response_text.lower() for keyword in secure_keywords)

def check_otp_required(response_text):
    otp_keywords = [
        "otp", "one-time password", "verification code", "enter the code", 
        "authentication code", "sms code", "mobile verification"
    ]
    return any(keyword in response_text.lower() for keyword in otp_keywords)

def check_cvv_required(response_text):
    response_text = response_text.lower()
    cvv_required = "cvv" in response_text
    cvc_required = "cvc" in response_text
    if cvv_required and cvc_required:
        return "Both CVV and CVC Required"
    elif cvv_required:
        return "CVV Required"
    elif cvc_required:
        return "CVC Required"
    else:
        return "None"

def check_inbuilt_payment_system(response_text):
    inbuilt_keywords = ["native payment", "integrated payment", "built-in checkout", "secure payment on this site", "on-site payment", "internal payment gateway"]
    return any(keyword in response_text.lower() for keyword in inbuilt_keywords)

# Core function to check URL for various attributes
def check_url(url):
    if not is_valid_url(url):
        return ["Invalid URL"], 400, False, False, "N/A", "N/A", "N/A"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        detected_gateways = find_payment_gateways(response.text)
        captcha_detected = check_captcha(response.text)
        cloudflare_detected = check_cloudflare(response.text)
        is_3d_secure = check_3d_secure(response.text)
        is_otp_required = check_otp_required(response.text)
        cvv_cvc_status = check_cvv_required(response.text)
        inbuilt_payment = check_inbuilt_payment_system(response.text)

        payment_security_type = (
            "Both 3D Secure and OTP Required" if is_3d_secure and is_otp_required else
            "3D Secure" if is_3d_secure else
            "OTP Required" if is_otp_required else
            "2D (No extra security)"
        )
        if captcha_detected:
            payment_security_type += " | Captcha Detected"
        if cloudflare_detected:
            payment_security_type += " | Protected by Cloudflare"

        inbuilt_status = "Yes" if inbuilt_payment else "No"

        # Update bot statistics
        bot_stats["total_checks"] += 1
        bot_stats["unique_urls"].add(url)

        return detected_gateways, response.status_code, captcha_detected, cloudflare_detected, payment_security_type, cvv_cvc_status, inbuilt_status

    except requests.exceptions.RequestException as e:
        return [f"Error: {str(e)}"], 500, False, False, "N/A", "N/A", "N/A"

# Bot command to start and show welcome message
@bot.message_handler(commands=['start'])
def cmd_start(message):
    welcome_message = (
        "➻ Welcome To Oᴠᴇʀ ❖ Sᴛʀɪᴘᴇ\n"
        "Incline Developer - [@TechPiro](https://t.me/TechPiro)\n"
        "Do /register to start."
    )
    bot.send_message(message.chat.id, welcome_message, parse_mode="Markdown")

# Bot command to register and prompt user to enter a URL
@bot.message_handler(commands=['register'])
def cmd_register(message):
    bot.send_message(message.chat.id, "Enter the URL you want to check:")

# Bot command to display statistics about the bot usage
@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    total_checks = bot_stats["total_checks"]
    unique_urls_count = len(bot_stats["unique_urls"])
    
    stats_message = (
        f"📊 **Bot Statistics**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🔹 Total URL Checks: {total_checks}\n"
        f"🔹 Unique URLs Analyzed: {unique_urls_count}\n"
        f"\nBot by [@TechPiro](https://t.me/TechPiro)"
    )
    bot.send_message(message.chat.id, stats_message, parse_mode="Markdown")

# Handler for text messages to process URL check
@bot.message_handler(content_types=['text'])
def handle_text(message):
    url = message.text.strip()
    detected_gateways, status_code, captcha, cloudflare, payment_security_type, cvv_cvc_status, inbuilt_status = check_url(url)

    gateways_str = ', '.join(detected_gateways) if detected_gateways else "None"
    response_message = (
        f"🔍 Gateways Fetched Successfully ✅\n"
        f"━━━━━━━━━━━━━━\n"
        f"🔹 URL: {url}\n"
        f"🔹 Payment Gateways: {gateways_str}\n"
        f"🔹 Captcha Detected: {captcha}\n"
        f"🔹 Cloudflare Detected: {cloudflare}\n"
        f"🔹 Payment Security Type: {payment_security_type}\n"
        f"🔹 CVV/CVC Requirement: {cvv_cvc_status}\n"
        f"🔹 Inbuilt Payment System: {inbuilt_status}\n"
        f"🔹 Status Code: {status_code}\n"
        f"\nBot by [@TechPiro](https://t.me/TechPiro)"
    )
    
    bot.send_message(message.chat.id, response_message, parse_mode="Markdown")

# Start polling for bot commands and messages
bot.polling()
  
