import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

print("=== Gmail SMTP Connection Test ===\n")

mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
mail_port = int(os.getenv('MAIL_PORT', 587))
mail_username = os.getenv('MAIL_USERNAME')
mail_password = os.getenv('MAIL_PASSWORD')

print(f"Server: {mail_server}")
print(f"Port: {mail_port}")
print(f"Username: {mail_username}")
print(f"Password: {'*' * len(mail_password) if mail_password else 'NOT SET'} (length: {len(mail_password) if mail_password else 0})")
print()

try:
    print("Step 1: Connecting to SMTP server...")
    server = smtplib.SMTP(mail_server, mail_port, timeout=30)
    print("✓ Connected successfully\n")
    
    print("Step 2: Starting TLS encryption...")
    server.starttls()
    print("✓ TLS started successfully\n")
    
    print("Step 3: Authenticating with Gmail...")
    server.login(mail_username, mail_password)
    print("✓ Authentication successful\n")
    
    print("Step 4: Sending test email...")
    msg = MIMEMultipart()
    msg['Subject'] = 'Test Email from Varon OTP System'
    msg['From'] = mail_username
    msg['To'] = input("Enter recipient email: ")
    
    body = MIMEText("This is a test email from the Varon OTP system. If you receive this, your email configuration is working correctly!", 'plain')
    msg.attach(body)
    
    server.send_message(msg)
    print("✓ Email sent successfully!\n")
    
    server.quit()
    print("=== All tests passed! ===")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"✗ Authentication failed: {e}")
    print("\nPossible issues:")
    print("1. App password is incorrect")
    print("2. 2-Factor Authentication not enabled on Gmail")
    print("3. App password not generated correctly")
    print("\nTo fix:")
    print("- Go to https://myaccount.google.com/apppasswords")
    print("- Generate a NEW app password")
    print("- Copy the 16-character password (no spaces)")
    print("- Update MAIL_PASSWORD in .env file")
    
except smtplib.SMTPConnectError as e:
    print(f"✗ Connection failed: {e}")
    print("\nPossible issues:")
    print("1. Internet connection problem")
    print("2. Firewall blocking SMTP")
    print("3. Gmail servers unreachable")
    
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
