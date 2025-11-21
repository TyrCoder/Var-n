import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from utils.otp_service import OTPService

load_dotenv()

print("\n" + "="*50)
print("Varón Email-to-SMS OTP Test")
print("="*50)

print("\nSupported Carriers:")
print("Philippine carriers: smart, globe, sun, tnt, tm, dito")
print("US carriers: att, tmobile, verizon, sprint")

phone = input("\nEnter phone number (without +63 or 0): ")
carrier = input("Enter carrier (e.g., smart, globe, tm): ").strip().lower()

otp = OTPService.generate_otp()
print(f"\nGenerated OTP: {otp}")
print(f"Sending SMS to {phone} via {carrier} email gateway...")

try:
    success = OTPService.send_sms_via_email(phone, otp, purpose='registration', carrier=carrier)

    if success:
        print("\n✓ SMS sent successfully via email!")
        print(f"\nThe SMS should arrive at {phone} within 1-2 minutes.")
        print("Note: Email-to-SMS gateways may have delays or may not work")
        print("if the carrier has disabled this feature.")
    else:
        print("\n✗ Failed to send SMS")
        print("\nTroubleshooting:")
        print("1. Check if carrier name is correct")
        print("2. Verify phone number format (10 digits without prefix)")
        print("3. Some carriers have disabled email-to-SMS gateways")
        print("4. Consider using Semaphore or Twilio for reliable SMS delivery")
except Exception as e:
    print(f"\n✗ Error occurred: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
