"""
Test script for OTP functionality
Run this after configuring your .env file
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.otp_service import OTPService
from dotenv import load_dotenv

load_dotenv()

def test_email_otp():
    """Test email OTP sending"""
    print("\n" + "="*50)
    print("Testing Email OTP")
    print("="*50)
    
    test_email = input("Enter your email address to test: ").strip()
    
    if not test_email or '@' not in test_email:
        print("Invalid email address!")
        return False
    
    otp_code = OTPService.generate_otp(6)
    print(f"\nGenerated OTP: {otp_code}")
    print("Sending email...")
    
    success = OTPService.send_email_otp(test_email, otp_code, 'registration')
    
    if success:
        print(f"✓ Email sent successfully to {test_email}")
        print(f"✓ Check your inbox for OTP: {otp_code}")
        return True
    else:
        print("✗ Failed to send email")
        print("\nPossible issues:")
        print("1. Check MAIL_USERNAME and MAIL_PASSWORD in .env")
        print("2. Make sure you're using a Gmail App Password (not your regular password)")
        print("3. Check your internet connection")
        return False

def test_sms_otp():
    """Test SMS OTP sending"""
    print("\n" + "="*50)
    print("Testing SMS OTP")
    print("="*50)
    
    test_phone = input("Enter your phone number (with country code, e.g., +639123456789): ").strip()
    
    if not test_phone or not test_phone.startswith('+'):
        print("Invalid phone number! Use format: +639123456789")
        return False
    
    otp_code = OTPService.generate_otp(6)
    print(f"\nGenerated OTP: {otp_code}")
    print("Sending SMS...")
    
    success = OTPService.send_sms_otp(test_phone, otp_code, 'registration')
    
    if success:
        print(f"✓ SMS sent successfully to {test_phone}")
        print(f"✓ Check your phone for OTP: {otp_code}")
        return True
    else:
        print("✗ Failed to send SMS")
        print("\nPossible issues:")
        print("1. No SMS provider configured (SEMAPHORE_API_KEY or TWILIO credentials)")
        print("2. Check provider credentials in .env")
        print("3. Check if you have sufficient credits")
        return False

def main():
    """Main test function"""
    print("\n" + "="*50)
    print("Varón OTP Test Suite")
    print("="*50)
    
    print("\nSelect test option:")
    print("1. Test Email OTP")
    print("2. Test SMS OTP")
    print("3. Test Both")
    print("0. Exit")
    
    choice = input("\nEnter your choice: ").strip()
    
    if choice == '1':
        test_email_otp()
    elif choice == '2':
        test_sms_otp()
    elif choice == '3':
        email_ok = test_email_otp()
        sms_ok = test_sms_otp()
        print("\n" + "="*50)
        print("Test Summary")
        print("="*50)
        print(f"Email OTP: {'✓ PASSED' if email_ok else '✗ FAILED'}")
        print(f"SMS OTP: {'✓ PASSED' if sms_ok else '✗ FAILED'}")
    elif choice == '0':
        print("Exiting...")
        return
    else:
        print("Invalid choice!")
        return
    
    print("\n" + "="*50)
    print("Test completed!")
    print("="*50)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
