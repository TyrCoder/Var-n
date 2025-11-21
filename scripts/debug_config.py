import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

print("Direct from os.getenv:")
print(f"MAIL_USERNAME: {os.getenv('MAIL_USERNAME')}")
print(f"MAIL_PASSWORD: {os.getenv('MAIL_PASSWORD')}")
print(f"MAIL_PASSWORD length: {len(os.getenv('MAIL_PASSWORD', ''))}")

from config import Config

print("\nFrom Config class:")
print(f"MAIL_USERNAME: {Config.MAIL_USERNAME}")
print(f"MAIL_PASSWORD: {Config.MAIL_PASSWORD}")
print(f"MAIL_PASSWORD length: {len(Config.MAIL_PASSWORD)}")

print("\nTesting direct SMTP login:")
import smtplib

try:
    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
    server.starttls()
    
    print(f"\nAttempting login with Config.MAIL_PASSWORD: {Config.MAIL_PASSWORD[:4]}...{Config.MAIL_PASSWORD[-4:]}")
    server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
    print("✓ Login successful with Config password!")
    server.quit()
except Exception as e:
    print(f"✗ Login failed: {e}")
