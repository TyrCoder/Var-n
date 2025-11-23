import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mysql.connector
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OTPService:
    """OTP Service for email and SMS verification"""

    # Email configuration from .env
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@varon.com')

    # SMS configuration
    SEMAPHORE_API_KEY = os.getenv('SEMAPHORE_API_KEY')
    SEMAPHORE_SENDER_NAME = os.getenv('SEMAPHORE_SENDER_NAME', 'VARON')

    # Twilio configuration (alternative)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

    @staticmethod
    def generate_otp(length=6):
        """Generate a random OTP code"""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def create_otp_record(conn, email=None, phone=None, otp_type='email', purpose='registration', ip_address=None):
        """
        Create and store OTP record in database

        Args:
            conn: Database connection
            email: Email address for email OTP
            phone: Phone number for SMS OTP
            otp_type: 'email' or 'sms'
            purpose: Purpose of OTP (registration, login, password_reset, etc.)
            ip_address: IP address of the request

        Returns:
            tuple: (otp_code, otp_id) or (None, None) on failure
        """
        try:
            cursor = conn.cursor()

            # Generate OTP
            otp_code = OTPService.generate_otp()

            # Calculate expiry (10 minutes from now)
            expires_at = datetime.now() + timedelta(minutes=10)

            # Insert OTP record
            cursor.execute('''
                INSERT INTO otp_verifications
                (email, phone, otp_code, otp_type, purpose, expires_at, ip_address, attempts, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0, FALSE)
            ''', (email, phone, otp_code, otp_type, purpose, expires_at, ip_address))

            otp_id = cursor.lastrowid
            conn.commit()
            cursor.close()

            return otp_code, otp_id

        except Exception as e:
            print(f"Error creating OTP record: {e}")
            return None, None

    @staticmethod
    def send_email_otp(email, otp_code, purpose='registration'):
        """
        Send OTP via email

        Args:
            email: Recipient email address
            otp_code: The OTP code to send
            purpose: Purpose of the OTP

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = OTPService.MAIL_DEFAULT_SENDER
            msg['To'] = email
            msg['Subject'] = f'Varón - Your OTP Code'

            # Email body
            purpose_text = {
                'registration': 'account registration',
                'login': 'login verification',
                'password_reset': 'password reset'
            }.get(purpose, 'verification')

            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #0a0a0a; margin: 0;">Varón Apparel</h1>
                    <p style="color: #666; margin: 10px 0;">Your One-Time Password</p>
                </div>

                <div style="background: #f8f8f8; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #0a0a0a; margin: 0 0 20px 0; font-size: 24px;">{otp_code}</h2>
                    <p style="color: #666; margin: 0; font-size: 16px;">Use this code to complete your {purpose_text}</p>
                </div>

                <div style="color: #666; font-size: 14px; line-height: 1.5;">
                    <p><strong>Important:</strong></p>
                    <ul style="text-align: left; padding-left: 20px;">
                        <li>This code will expire in 10 minutes</li>
                        <li>Do not share this code with anyone</li>
                        <li>If you didn't request this code, please ignore this email</li>
                    </ul>
                </div>

                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px;">
                    <p>This is an automated message from Varón Apparel. Please do not reply to this email.</p>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(body, 'html'))

            # Send email
            server = smtplib.SMTP(OTPService.MAIL_SERVER, OTPService.MAIL_PORT)
            if OTPService.MAIL_USE_TLS:
                server.starttls()
            server.login(OTPService.MAIL_USERNAME, OTPService.MAIL_PASSWORD)
            server.sendmail(OTPService.MAIL_DEFAULT_SENDER, email, msg.as_string())
            server.quit()

            print(f"OTP email sent successfully to {email}")
            return True

        except Exception as e:
            print(f"Error sending OTP email: {e}")
            return False

    @staticmethod
    def send_sms_otp(phone, otp_code, purpose='registration'):
        """
        Send OTP via SMS using Semaphore API

        Args:
            phone: Phone number (should start with country code, e.g., +63 for Philippines)
            otp_code: The OTP code to send
            purpose: Purpose of the OTP

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not OTPService.SEMAPHORE_API_KEY:
                print("Semaphore API key not configured")
                return False

            # Format phone number (ensure it starts with country code)
            if phone.startswith('0'):
                phone = '+63' + phone[1:]  # Convert Philippine numbers
            elif not phone.startswith('+'):
                phone = '+63' + phone

            purpose_text = {
                'registration': 'account registration',
                'login': 'login verification',
                'password_reset': 'password reset'
            }.get(purpose, 'verification')

            message = f"Varón: Your OTP code is {otp_code}. Use this to complete your {purpose_text}. Valid for 10 minutes."

            # Send via Semaphore API
            response = requests.post(
                'https://api.semaphore.co/api/v4/messages',
                data={
                    'apikey': OTPService.SEMAPHORE_API_KEY,
                    'number': phone,
                    'message': message,
                    'sendername': OTPService.SEMAPHORE_SENDER_NAME
                }
            )

            if response.status_code == 200:
                print(f"OTP SMS sent successfully to {phone}")
                return True
            else:
                print(f"Failed to send SMS: {response.text}")
                return False

        except Exception as e:
            print(f"Error sending OTP SMS: {e}")
            return False

    @staticmethod
    def verify_otp(conn, otp_code, email=None, phone=None, purpose=None):
        """
        Verify OTP code

        Args:
            conn: Database connection
            otp_code: The OTP code to verify
            email: Email address (for email OTP)
            phone: Phone number (for SMS OTP)
            purpose: Purpose of the OTP

        Returns:
            tuple: (is_valid, message)
        """
        try:
            cursor = conn.cursor(dictionary=True)

            # Find the OTP record
            query = """
                SELECT id, otp_code, expires_at, attempts, is_verified
                FROM otp_verifications
                WHERE otp_code = %s AND expires_at > NOW() AND is_verified = FALSE
            """

            params = [otp_code]

            if email:
                query += " AND email = %s"
                params.append(email)
            elif phone:
                query += " AND phone = %s"
                params.append(phone)

            if purpose:
                query += " AND purpose = %s"
                params.append(purpose)

            query += " ORDER BY created_at DESC LIMIT 1"

            cursor.execute(query, params)
            otp_record = cursor.fetchone()

            if not otp_record:
                cursor.close()
                return False, "Invalid or expired OTP code"

            # Check attempts
            if otp_record['attempts'] >= 3:
                cursor.close()
                return False, "Too many failed attempts. Please request a new OTP"

            # Mark as verified
            cursor.execute(
                "UPDATE otp_verifications SET is_verified = TRUE, verified_at = NOW(), attempts = attempts + 1 WHERE id = %s",
                (otp_record['id'],)
            )

            conn.commit()
            cursor.close()

            return True, "OTP verified successfully"

        except Exception as e:
            print(f"Error verifying OTP: {e}")
            return False, "Verification failed"

    @staticmethod
    def increment_attempt(conn, otp_code, email=None, phone=None):
        """
        Increment failed attempt count

        Args:
            conn: Database connection
            otp_code: The OTP code
            email: Email address
            phone: Phone number
        """
        try:
            cursor = conn.cursor()

            query = "UPDATE otp_verifications SET attempts = attempts + 1 WHERE otp_code = %s"
            params = [otp_code]

            if email:
                query += " AND email = %s"
                params.append(email)
            elif phone:
                query += " AND phone = %s"
                params.append(phone)

            cursor.execute(query, params)
            conn.commit()
            cursor.close()

        except Exception as e:
            print(f"Error incrementing OTP attempt: {e}")

    @staticmethod
    def cleanup_expired_otps(conn):
        """
        Clean up expired OTP records (optional maintenance function)

        Args:
            conn: Database connection
        """
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM otp_verifications WHERE expires_at < NOW() OR is_verified = TRUE")
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            print(f"Cleaned up {deleted_count} expired OTP records")
        except Exception as e:
            print(f"Error cleaning up OTP records: {e}")