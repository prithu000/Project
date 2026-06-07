"""
OTP generation and verification utilities
"""
import random
import time
from datetime import datetime, timedelta


# In-memory OTP storage (use Redis/database in production)
OTP_STORAGE = {}


def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))


def send_otp_sms(phone, otp):
    """
    Send OTP via SMS
    
    For production, integrate with:
    - Twilio
    - MSG91
    - Fast2SMS
    - AWS SNS
    
    For now, just print to console (development mode)
    """
    print(f"\n{'='*50}")
    print(f"📱 SMS to {phone}")
    print(f"🔐 Your CamCap OTP is: {otp}")
    print(f"⏰ Valid for 5 minutes")
    print(f"{'='*50}\n")
    
    # TODO: In production, add actual SMS gateway integration:
    # Example with MSG91:
    # import requests
    # url = f"https://api.msg91.com/api/v5/otp?mobile={phone}&otp={otp}"
    # requests.get(url, headers={'authkey': 'YOUR_AUTH_KEY'})
    
    return True


def store_otp(phone, otp):
    """Store OTP with expiry time (5 minutes)"""
    expiry = datetime.now() + timedelta(minutes=5)
    OTP_STORAGE[phone] = {
        'otp': otp,
        'expiry': expiry,
        'attempts': 0
    }


def verify_otp(phone, otp):
    """Verify OTP for given phone number"""
    if phone not in OTP_STORAGE:
        return False, "OTP not found. Please request a new OTP."
    
    stored_data = OTP_STORAGE[phone]
    
    # Check expiry
    if datetime.now() > stored_data['expiry']:
        del OTP_STORAGE[phone]
        return False, "OTP expired. Please request a new OTP."
    
    # Check attempts (max 3)
    if stored_data['attempts'] >= 3:
        del OTP_STORAGE[phone]
        return False, "Too many failed attempts. Please request a new OTP."
    
    # Verify OTP
    if stored_data['otp'] == otp:
        del OTP_STORAGE[phone]
        return True, "OTP verified successfully!"
    else:
        stored_data['attempts'] += 1
        remaining = 3 - stored_data['attempts']
        return False, f"Invalid OTP. {remaining} attempts remaining."


def cleanup_expired_otps():
    """Remove expired OTPs from storage"""
    current_time = datetime.now()
    expired_phones = [
        phone for phone, data in OTP_STORAGE.items()
        if current_time > data['expiry']
    ]
    for phone in expired_phones:
        del OTP_STORAGE[phone]
