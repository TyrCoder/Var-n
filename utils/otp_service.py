import random
import string
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

class OTPService:
    @staticmethod
    def generate_otp(length=6):
        """Generate a random numeric OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def send_email_otp(email, otp_code, purpose='registration'):
        """Send OTP via email using SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Your Varón Verification Code - {otp_code}'
            msg['From'] = Config.MAIL_DEFAULT_SENDER
            msg['To'] = email
            
            purpose_text = {
                'registration': 'complete your registration',
                'login': 'log in to your account',
                'password_reset': 'reset your password',
                'phone_verify': 'verify your phone number'
            }
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
                <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f5f5f5; padding: 40px 0;">
                    <tr>
                        <td align="center">
                            <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                <tr>
                                    <td style="padding: 40px 40px 20px;">
                                        <h1 style="margin: 0 0 20px; font-size: 28px; font-weight: 600; color: #000000; font-family: 'Playfair Display', Georgia, serif;">Varón</h1>
                                        <h2 style="margin: 0 0 20px; font-size: 22px; font-weight: 500; color: #333333;">Verification Code</h2>
                                        <p style="margin: 0 0 30px; font-size: 16px; line-height: 1.6; color: #666666;">
                                            Use this code to {purpose_text.get(purpose, 'verify your account')}:
                                        </p>
                                        <div style="background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); border-radius: 12px; padding: 30px; text-align: center; margin: 30px 0;">
                                            <div style="font-size: 40px; font-weight: 700; letter-spacing: 8px; color: #000000; font-family: 'Courier New', monospace;">
                                                {otp_code}
                                            </div>
                                        </div>
                                        <p style="margin: 0 0 20px; font-size: 14px; line-height: 1.6; color: #999999;">
                                            This code will expire in {Config.OTP_EXPIRY_MINUTES} minutes. For your security, do not share this code with anyone.
                                        </p>
                                        <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #999999;">
                                            If you didn't request this code, please ignore this email.
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px 40px 40px; border-top: 1px solid #e5e5e5;">
                                        <p style="margin: 0; font-size: 12px; color: #999999; text-align: center;">
                                            © {datetime.now().year} Varón. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            part = MIMEText(html, 'html')
            msg.attach(part)
            
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Email sending error: {str(e)}")
            return False
    
    @staticmethod
    def send_sms_via_email(phone, otp_code, purpose='registration', carrier='smart'):
        """Send SMS via email-to-SMS gateway (Free method)"""
        try:
            carrier_gateways = {
                'smart': '@sms.smart.com.ph',
                'globe': '@sms.globe.com.ph',
                'sun': '@mysuntext.com.ph',
                'tnt': '@sms.globe.com.ph',
                'tm': '@sms.smart.com.ph',
                'dito': '@dito.ph',
                'cherry': '@sms.cherry.ph',
                'att': '@txt.att.net',
                'tmobile': '@tmomail.net',
                'verizon': '@vtext.com',
                'sprint': '@messaging.sprintpcs.com',
                'boost': '@sms.myboostmobile.com',
                'cricket': '@mms.cricketwireless.net',
                'metropcs': '@mymetropcs.com'
            }
            
            carrier_lower = carrier.lower()
            if carrier_lower not in carrier_gateways:
                print(f"Unsupported carrier: {carrier}")
                print(f"Supported carriers: {', '.join(carrier_gateways.keys())}")
                return False
            
            phone_clean = ''.join(filter(str.isdigit, phone))
            if phone_clean.startswith('63'):
                phone_clean = phone_clean[2:]
            elif phone_clean.startswith('+63'):
                phone_clean = phone_clean[3:]
            elif phone_clean.startswith('0'):
                phone_clean = phone_clean[1:]
            
            if not phone_clean or len(phone_clean) != 10:
                print(f"Invalid phone number format. Expected 10 digits, got: {phone_clean}")
                return False
            
            sms_email = phone_clean + carrier_gateways[carrier_lower]
            
            purpose_text = {
                'registration': 'registration',
                'login': 'login',
                'password_reset': 'password reset',
                'phone_verify': 'phone verification'
            }
            
            message = f"Your Varon {purpose_text.get(purpose, 'verification')} code is: {otp_code}. Valid for {Config.OTP_EXPIRY_MINUTES} minutes."
            
            msg = MIMEMultipart()
            msg['Subject'] = 'Varon OTP'
            msg['From'] = Config.MAIL_USERNAME
            msg['To'] = sms_email
            
            part = MIMEText(message, 'plain')
            msg.attach(part)
            
            print(f"Connecting to {Config.MAIL_SERVER}:{Config.MAIL_PORT}")
            print(f"Username: {Config.MAIL_USERNAME}")
            print(f"Password length: {len(Config.MAIL_PASSWORD)}")
            
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=30) as server:
                print("Starting TLS...")
                server.starttls()
                print(f"Logging in with password: {Config.MAIL_PASSWORD[:4]}...{Config.MAIL_PASSWORD[-4:]}")
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                print("Sending message...")
                server.send_message(msg)
            
            print(f"SMS sent via email to {sms_email}")
            return True
        except Exception as e:
            print(f"SMS via email error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def send_sms_otp_semaphore(phone, otp_code, purpose='registration'):
        """Send OTP via SMS using Semaphore (Philippines)"""
        try:
            if not Config.SEMAPHORE_API_KEY:
                print("Semaphore API key not configured")
                return False
            
            purpose_text = {
                'registration': 'registration',
                'login': 'login',
                'password_reset': 'password reset',
                'phone_verify': 'phone verification'
            }
            
            message = f"Your Varon {purpose_text.get(purpose, 'verification')} code is: {otp_code}. Valid for {Config.OTP_EXPIRY_MINUTES} minutes. Do not share this code."
            
            url = 'https://api.semaphore.co/api/v4/messages'
            payload = {
                'apikey': Config.SEMAPHORE_API_KEY,
                'number': phone,
                'message': message,
                'sendername': Config.SEMAPHORE_SENDER_NAME
            }
            
            response = requests.post(url, data=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"SMS sending error (Semaphore): {str(e)}")
            return False
    
    @staticmethod
    def send_sms_otp_twilio(phone, otp_code, purpose='registration'):
        """Send OTP via SMS using Twilio"""
        try:
            if not Config.TWILIO_ACCOUNT_SID or not Config.TWILIO_AUTH_TOKEN:
                print("Twilio credentials not configured")
                return False
            
            from twilio.rest import Client
            
            purpose_text = {
                'registration': 'registration',
                'login': 'login',
                'password_reset': 'password reset',
                'phone_verify': 'phone verification'
            }
            
            message = f"Your Varon {purpose_text.get(purpose, 'verification')} code is: {otp_code}. Valid for {Config.OTP_EXPIRY_MINUTES} minutes."
            
            client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=message,
                from_=Config.TWILIO_PHONE_NUMBER,
                to=phone
            )
            
            return True
        except Exception as e:
            print(f"SMS sending error (Twilio): {str(e)}")
            return False
    
    @staticmethod
    def send_sms_otp(phone, otp_code, purpose='registration', carrier='smart'):
        """Send OTP via SMS using available provider"""
        if Config.SEMAPHORE_API_KEY:
            return OTPService.send_sms_otp_semaphore(phone, otp_code, purpose)
        elif Config.TWILIO_ACCOUNT_SID:
            return OTPService.send_sms_otp_twilio(phone, otp_code, purpose)
        else:
            print("Using free email-to-SMS gateway")
            return OTPService.send_sms_via_email(phone, otp_code, purpose, carrier)
    
    @staticmethod
    def create_otp_record(conn, email=None, phone=None, user_id=None, otp_type='email', purpose='registration', ip_address=None):
        """Create OTP record in database"""
        try:
            cursor = conn.cursor()
            otp_code = OTPService.generate_otp(Config.OTP_LENGTH)
            expires_at = datetime.now() + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
            
            cursor.execute('''
                INSERT INTO otp_verifications (
                    user_id, email, phone, otp_code, otp_type, 
                    purpose, expires_at, ip_address
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (user_id, email, phone, otp_code, otp_type, purpose, expires_at, ip_address))
            
            conn.commit()
            otp_id = cursor.lastrowid
            cursor.close()
            
            return otp_code, otp_id
        except Exception as e:
            print(f"Error creating OTP record: {str(e)}")
            return None, None
    
    @staticmethod
    def verify_otp(conn, otp_code, email=None, phone=None, purpose='registration'):
        """Verify OTP code"""
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = '''
                SELECT * FROM otp_verifications 
                WHERE otp_code = %s AND purpose = %s 
                AND is_verified = FALSE 
                AND expires_at > NOW()
                AND attempts < %s
            '''
            params = [otp_code, purpose, Config.OTP_MAX_ATTEMPTS]
            
            if email:
                query += ' AND email = %s'
                params.append(email)
            elif phone:
                query += ' AND phone = %s'
                params.append(phone)
            
            query += ' ORDER BY created_at DESC LIMIT 1'
            
            cursor.execute(query, params)
            otp_record = cursor.fetchone()
            
            if not otp_record:
                cursor.close()
                return False, "Invalid or expired OTP code"
            
            cursor.execute('''
                UPDATE otp_verifications 
                SET is_verified = TRUE, verified_at = NOW()
                WHERE id = %s
            ''', (otp_record['id'],))
            
            if otp_record['user_id']:
                if otp_record['otp_type'] == 'email':
                    cursor.execute('''
                        UPDATE users 
                        SET email_verified = TRUE, email_verified_at = NOW()
                        WHERE id = %s
                    ''', (otp_record['user_id'],))
                elif otp_record['otp_type'] == 'sms':
                    cursor.execute('''
                        UPDATE users 
                        SET phone_verified = TRUE, phone_verified_at = NOW()
                        WHERE id = %s
                    ''', (otp_record['user_id'],))
            
            conn.commit()
            cursor.close()
            
            return True, "OTP verified successfully"
        except Exception as e:
            print(f"Error verifying OTP: {str(e)}")
            return False, "Verification failed"
    
    @staticmethod
    def increment_attempt(conn, otp_code, email=None, phone=None):
        """Increment OTP attempt counter"""
        try:
            cursor = conn.cursor()
            
            query = 'UPDATE otp_verifications SET attempts = attempts + 1 WHERE otp_code = %s'
            params = [otp_code]
            
            if email:
                query += ' AND email = %s'
                params.append(email)
            elif phone:
                query += ' AND phone = %s'
                params.append(phone)
            
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Error incrementing attempt: {str(e)}")
    
    @staticmethod
    def cleanup_expired_otps(conn):
        """Remove expired OTP records"""
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM otp_verifications WHERE expires_at < NOW()')
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Error cleaning up OTPs: {str(e)}")
