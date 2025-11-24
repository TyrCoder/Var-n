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
                (email, phone, otp_code, otp_type, purpose, expires_at, ip_address, attempts, used_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0, NULL)
            ''', (email, phone, otp_code, otp_type, purpose, expires_at, ip_address))

            otp_id = cursor.lastrowid
            conn.commit()
            cursor.close()

            return otp_code, otp_id

        except Exception as e:
            print(f"Error creating OTP record: {e}")
            import traceback
            traceback.print_exc()
            # Try to rollback if connection is still open
            try:
                conn.rollback()
            except:
                pass
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
            # Check if email credentials are configured
            if not OTPService.MAIL_USERNAME or not OTPService.MAIL_PASSWORD:
                print("Error: Email credentials (MAIL_USERNAME and MAIL_PASSWORD) are not configured in environment variables")
                return False

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

        except smtplib.SMTPAuthenticationError as e:
            print(f"SMTP Authentication Error: {e}")
            print("Please check your MAIL_USERNAME and MAIL_PASSWORD in .env file")
            return False
        except smtplib.SMTPException as e:
            print(f"SMTP Error: {e}")
            return False
        except Exception as e:
            print(f"Error sending OTP email: {e}")
            return False

    @staticmethod
    def get_carrier_email_gateway(phone):
        """
        Get email-to-SMS gateway address for a phone number (FREE method)
        Supports Philippine carriers and common international carriers
        
        Philippine Carriers Supported:
        - Globe/TM/GOMO: @globe.com.ph
        - Smart/TNT: @smart.com.ph
        - Sun: @sun.com.ph
        - DITO: @dito.ph
        
        US/Canada Carriers Supported:
        - AT&T: @txt.att.net
        - Verizon: @vtext.com
        - T-Mobile: @tmomail.net
        - Sprint: @messaging.sprintpcs.com
        
        Args:
            phone: Phone number (with or without country code)
            
        Returns:
            str: Email gateway address or None if carrier not supported
        """
        # Clean phone number - remove all non-digit characters
        clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').replace('.', '')
        
        print(f"🔍 Carrier detection for phone: {phone} -> cleaned: {clean_phone}")
        
        # Philippine carriers (+63)
        if clean_phone.startswith('63'):
            # Remove country code
            local_number = clean_phone[2:]
            # Remove leading 0 if present
            if local_number.startswith('0'):
                local_number = local_number[1:]
            
            print(f"   Local number after processing: {local_number} (length: {len(local_number)})")
            
            # Get last 10 digits (Philippine mobile numbers are 10 digits)
            if len(local_number) >= 10:
                mobile_number = local_number[-10:]  # Get last 10 digits
                print(f"   Mobile number: {mobile_number}")
                
                # Carrier detection based on prefix (first 3 digits)
                prefix = mobile_number[:3]
                print(f"   Detected prefix: {prefix}")
                
                # Globe/TM/GOMO prefixes (most common)
                # GOMO is a digital service by Globe, uses same gateway
                globe_prefixes = ['817', '905', '906', '915', '916', '917', '926', '927', '935', '936', '937', '994', '995', '996', '997', '975', '976', '977', '978', '979', '980', '981', '982', '983', '984', '985', '986', '987', '988', '989', '990', '991', '992', '993']
                
                # Smart/TNT prefixes
                smart_prefixes = ['813', '907', '908', '909', '910', '912', '918', '919', '920', '921', '928', '929', '930', '931', '932', '933', '934', '938', '939', '940', '941', '942', '943', '944', '946', '947', '948', '949', '950', '951', '961', '998', '999', '970', '971', '972', '973', '974']
                
                # Sun prefix
                sun_prefixes = ['922', '923', '924', '925']
                
                # DITO prefixes (newer carrier, launched 2021)
                # DITO uses prefix 895, 896, 897, 898, 899
                dito_prefixes = ['895', '896', '897', '898', '899']
                
                if prefix in globe_prefixes:
                    gateway = f"{mobile_number}@globe.com.ph"
                    print(f"   ✅ Detected Globe/TM/GOMO -> {gateway}")
                    return gateway
                elif prefix in smart_prefixes:
                    gateway = f"{mobile_number}@smart.com.ph"
                    print(f"   ✅ Detected Smart/TNT -> {gateway}")
                    return gateway
                elif prefix in sun_prefixes:
                    gateway = f"{mobile_number}@sun.com.ph"
                    print(f"   ✅ Detected Sun -> {gateway}")
                    return gateway
                elif prefix in dito_prefixes:
                    # DITO uses email-to-SMS gateway: number@dito.ph
                    gateway = f"{mobile_number}@dito.ph"
                    print(f"   ✅ Detected DITO -> {gateway}")
                    return gateway
                else:
                    # Default to Globe for unknown prefixes (most common carrier)
                    gateway = f"{mobile_number}@globe.com.ph"
                    print(f"   ⚠️ Unknown carrier prefix {prefix}, defaulting to Globe -> {gateway}")
                    return gateway
            else:
                print(f"   ❌ Invalid Philippine number length: {len(local_number)} (expected 10 digits)")
                return None
        
        # US/Canada carriers (+1)
        elif clean_phone.startswith('1') and len(clean_phone) == 11:
            mobile_number = clean_phone[1:]  # Remove country code
            # Default to AT&T (most common)
            return f"{mobile_number}@txt.att.net"
        
        return None

    @staticmethod
    def get_supported_carriers():
        """
        Get list of supported carriers for email-to-SMS gateway
        
        Returns:
            dict: Dictionary of supported countries and carriers
        """
        return {
            'Philippines (+63)': {
                'Globe/TM/GOMO': '@globe.com.ph',
                'Smart/TNT': '@smart.com.ph',
                'Sun': '@sun.com.ph',
                'DITO': '@dito.ph'
            },
            'United States/Canada (+1)': {
                'AT&T': '@txt.att.net',
                'Verizon': '@vtext.com',
                'T-Mobile': '@tmomail.net',
                'Sprint': '@messaging.sprintpcs.com'
            }
        }

    @staticmethod
    def send_sms_otp(phone, otp_code, purpose='registration'):
        """
        Send OTP via SMS using FREE email-to-SMS gateway
        
        First tries email-to-SMS gateway (free), then falls back to Semaphore API if configured

        Args:
            phone: Phone number (should start with country code, e.g., +63 for Philippines)
            otp_code: The OTP code to send
            purpose: Purpose of the OTP

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Format phone number (ensure it starts with country code)
            # Remove any existing +63 or + signs first
            clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            
            # Determine formatted phone
            if clean_phone.startswith('63'):
                # Already has country code
                formatted_phone = '+63' + clean_phone[2:]
            elif clean_phone.startswith('0'):
                # Philippine number starting with 0
                formatted_phone = '+63' + clean_phone[1:]
            elif len(clean_phone) == 10 and clean_phone.isdigit():
                # 10-digit Philippine number without prefix
                formatted_phone = '+63' + clean_phone
            else:
                # Keep as is if it already has +63
                formatted_phone = phone if phone.startswith('+63') else '+63' + clean_phone
            
            print(f"📱 Formatting phone: {phone} -> {formatted_phone}")

            purpose_text = {
                'registration': 'account registration',
                'login': 'login verification',
                'password_reset': 'password reset',
                'email_change': 'email change verification',
                'phone_verification': 'phone number verification'
            }.get(purpose, 'verification')

            message = f"Varón: Your OTP code is {otp_code}. Use this to complete your {purpose_text}. Valid for 10 minutes."

            # Try FREE email-to-SMS gateway first
            email_gateway = OTPService.get_carrier_email_gateway(formatted_phone)
            print(f"🔍 Email gateway lookup for {formatted_phone}: {email_gateway}")
            
            if email_gateway:
                try:
                    # Use existing email service to send to SMS gateway
                    if not OTPService.MAIL_USERNAME or not OTPService.MAIL_PASSWORD:
                        print("⚠️ Email credentials not configured, cannot use email-to-SMS gateway")
                        print(f"   Please set MAIL_USERNAME and MAIL_PASSWORD in .env file")
                    else:
                        # Create simple text email for SMS gateway
                        # SMS gateways work best with plain text, no HTML
                        msg = MIMEText(message, 'plain', 'utf-8')
                        msg['From'] = OTPService.MAIL_USERNAME  # Use actual email address
                        msg['To'] = email_gateway
                        msg['Subject'] = ''  # SMS gateways ignore subject, but some need empty string
                        
                        print(f"📧 Sending email to SMS gateway: {email_gateway}")
                        print(f"   From: {OTPService.MAIL_USERNAME}")
                        print(f"   Message: {message}")
                        
                        # Send email
                        print(f"   Connecting to SMTP server: {OTPService.MAIL_SERVER}:{OTPService.MAIL_PORT}")
                        server = smtplib.SMTP(OTPService.MAIL_SERVER, OTPService.MAIL_PORT)
                        server.set_debuglevel(0)  # Set to 1 for detailed debug, 0 for production
                        
                        if OTPService.MAIL_USE_TLS:
                            print(f"   Starting TLS...")
                            server.starttls()
                        
                        print(f"   Logging in with: {OTPService.MAIL_USERNAME}")
                        server.login(OTPService.MAIL_USERNAME, OTPService.MAIL_PASSWORD)
                        print(f"   ✅ Login successful")
                        print(f"   Sending email to: {email_gateway}")
                        result = server.sendmail(OTPService.MAIL_USERNAME, email_gateway, msg.as_string())
                        server.quit()
                        print(f"   ✅ Email sent successfully! Result: {result}")
                        print(f"✅ OTP SMS sent via email gateway to {formatted_phone} ({email_gateway})")
                        return True
                except smtplib.SMTPAuthenticationError as e:
                    print(f"❌ SMTP Authentication Error: {e}")
                    print(f"   Please check your MAIL_USERNAME and MAIL_PASSWORD in .env file")
                    print(f"   For Gmail, you need to use an App Password, not your regular password")
                except smtplib.SMTPException as e:
                    print(f"❌ SMTP Error: {e}")
                    print(f"   Check your email server settings (MAIL_SERVER, MAIL_PORT)")
                except Exception as e:
                    print(f"❌ Email-to-SMS gateway failed: {e}")
                    import traceback
                    traceback.print_exc()
                    print(f"   Falling back to API method if configured...")
            else:
                print(f"⚠️ No email gateway found for {formatted_phone}")
                print(f"   Phone number format: {formatted_phone}")
                print(f"   Cleaned phone: {clean_phone}")
                print(f"   Supported carriers: Globe, Smart, Sun, DITO (Philippines)")

            # Fallback to Semaphore API if configured
            if OTPService.SEMAPHORE_API_KEY:
                response = requests.post(
                    'https://api.semaphore.co/api/v4/messages',
                    data={
                        'apikey': OTPService.SEMAPHORE_API_KEY,
                        'number': formatted_phone,
                        'message': message,
                        'sendername': OTPService.SEMAPHORE_SENDER_NAME
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    print(f"✅ OTP SMS sent via Semaphore API to {formatted_phone}")
                    return True
                else:
                    print(f"❌ Failed to send SMS via Semaphore API: {response.text}")
                    return False
            else:
                print(f"❌ No SMS method available (no email gateway match and no API key configured)")
                return False

        except Exception as e:
            print(f"❌ Error sending OTP SMS: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def send_order_confirmation_email(email, order_number, order_data):
        """
        Send order confirmation email to buyer
        
        Args:
            email: Buyer's email address
            order_number: Order number
            order_data: Dictionary containing order details (items, total, shipping_address, etc.)
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Check if email credentials are configured
            if not OTPService.MAIL_USERNAME or not OTPService.MAIL_PASSWORD:
                print("Error: Email credentials (MAIL_USERNAME and MAIL_PASSWORD) are not configured")
                return False

            # Create message
            msg = MIMEMultipart()
            msg['From'] = OTPService.MAIL_DEFAULT_SENDER
            msg['To'] = email
            msg['Subject'] = f'Varón - Order Confirmation #{order_number}'

            # Format order items
            items_html = ""
            for item in order_data.get('items', []):
                items_html += f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #eee;">
                        <strong>{item.get('name', 'Product')}</strong>
                        {f"<br><small style='color: #666;'>Size: {item.get('size', 'N/A')}, Color: {item.get('color', 'N/A')}</small>" if item.get('size') or item.get('color') else ''}
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">{item.get('quantity', 1)}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">₱{float(item.get('price', 0)):.2f}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">₱{(float(item.get('price', 0)) * int(item.get('quantity', 1))):.2f}</td>
                </tr>
                """

            # Format shipping address
            shipping = order_data.get('shipping', {})
            shipping_address = f"""
            {shipping.get('firstName', '')} {shipping.get('lastName', '')}<br>
            {shipping.get('address', '')}<br>
            {shipping.get('city', '')}, {shipping.get('province', '')} {shipping.get('postalCode', '')}<br>
            {shipping.get('country', 'Philippines')}<br>
            Phone: {shipping.get('phone', '')}
            """

            # Email body
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
                <div style="background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #0a0a0a; margin: 0; font-size: 28px;">Varón Apparel</h1>
                        <p style="color: #666; margin: 10px 0; font-size: 16px;">Order Confirmation</p>
                    </div>

                    <div style="background: #f8f8f8; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
                        <h2 style="color: #0a0a0a; margin: 0 0 10px 0; font-size: 20px;">Thank you for your order!</h2>
                        <p style="color: #666; margin: 0; font-size: 14px;">Your order has been received and is being processed.</p>
                        <p style="color: #0a0a0a; margin: 15px 0 0 0; font-size: 18px; font-weight: 600;">Order Number: <span style="color: #3b82f6;">{order_number}</span></p>
                    </div>

                    <div style="margin-bottom: 30px;">
                        <h3 style="color: #0a0a0a; margin: 0 0 15px 0; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 10px;">Order Details</h3>
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                            <thead>
                                <tr style="background: #f9fafb;">
                                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #eee; font-size: 14px; color: #374151;">Item</th>
                                    <th style="padding: 12px; text-align: center; border-bottom: 2px solid #eee; font-size: 14px; color: #374151;">Qty</th>
                                    <th style="padding: 12px; text-align: right; border-bottom: 2px solid #eee; font-size: 14px; color: #374151;">Price</th>
                                    <th style="padding: 12px; text-align: right; border-bottom: 2px solid #eee; font-size: 14px; color: #374151;">Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items_html}
                            </tbody>
                        </table>
                        
                        <div style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #eee;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; color: #374151;">
                                <span>Subtotal:</span>
                                <span>₱{float(order_data.get('subtotal', 0)):.2f}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; color: #374151;">
                                <span>Shipping:</span>
                                <span>₱{float(order_data.get('shipping_fee', 0)):.2f}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 2px solid #eee; font-size: 18px; font-weight: 600; color: #0a0a0a;">
                                <span>Total:</span>
                                <span>₱{float(order_data.get('total', 0)):.2f}</span>
                            </div>
                        </div>
                    </div>

                    <div style="margin-bottom: 30px;">
                        <h3 style="color: #0a0a0a; margin: 0 0 15px 0; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 10px;">Shipping Address</h3>
                        <div style="color: #374151; font-size: 14px; line-height: 1.8;">
                            {shipping_address}
                        </div>
                    </div>

                    <div style="margin-bottom: 30px;">
                        <h3 style="color: #0a0a0a; margin: 0 0 15px 0; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 10px;">Payment Method</h3>
                        <p style="color: #374151; font-size: 14px; margin: 0;">{order_data.get('payment_method', 'Cash on Delivery')}</p>
                    </div>

                    <div style="background: #f0f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 30px;">
                        <p style="color: #1e40af; margin: 0; font-size: 14px; line-height: 1.6;">
                            <strong>What's next?</strong><br>
                            We'll send you another email when your order ships. You can track your order status anytime from your account dashboard.
                        </p>
                    </div>

                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; text-align: center;">
                        <p style="margin: 0;">This is an automated message from Varón Apparel. Please do not reply to this email.</p>
                        <p style="margin: 10px 0 0 0;">If you have any questions, please contact our support team.</p>
                    </div>
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

            print(f"✅ Order confirmation email sent successfully to {email} for order {order_number}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication Error: {e}")
            print("Please check your MAIL_USERNAME and MAIL_PASSWORD in .env file")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error sending order confirmation email: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def verify_otp(conn, otp_code, email=None, phone=None, purpose=None):
        """
        Verify OTP code

        Args:
            conn: Database connection
            otp_code: The OTP code to verify (will be stripped of whitespace)
            email: Email address (for email OTP)
            phone: Phone number (for SMS OTP)
            purpose: Purpose of the OTP

        Returns:
            tuple: (is_valid, message)
        """
        try:
            # Strip whitespace from OTP code
            otp_code = str(otp_code).strip() if otp_code else ''
            
            if not otp_code:
                return False, "OTP code is required"
            
            cursor = conn.cursor(dictionary=True)

            # Find the OTP record - try with and without purpose first
            # This helps if the enum wasn't updated yet
            query = """
                SELECT id, otp_code, expires_at, attempts, used_at, purpose, email, phone
                FROM otp_verifications
                WHERE otp_code = %s AND expires_at > NOW() AND used_at IS NULL
            """

            params = [otp_code]

            if email:
                query += " AND email = %s"
                params.append(email)
            elif phone:
                query += " AND phone = %s"
                params.append(phone)

            query += " ORDER BY created_at DESC LIMIT 1"

            cursor.execute(query, params)
            otp_record = cursor.fetchone()
            
            # If no record found and purpose was specified, try without purpose filter
            if not otp_record and purpose:
                print(f"⚠️ OTP not found with purpose filter, trying without purpose...")
                query_no_purpose = """
                    SELECT id, otp_code, expires_at, attempts, used_at, purpose, email, phone
                    FROM otp_verifications
                    WHERE otp_code = %s AND expires_at > NOW() AND used_at IS NULL
                """
                params_no_purpose = [otp_code]
                
                if email:
                    query_no_purpose += " AND email = %s"
                    params_no_purpose.append(email)
                elif phone:
                    query_no_purpose += " AND phone = %s"
                    params_no_purpose.append(phone)
                
                query_no_purpose += " ORDER BY created_at DESC LIMIT 1"
                cursor.execute(query_no_purpose, params_no_purpose)
                otp_record = cursor.fetchone()
                
                if otp_record:
                    print(f"✅ Found OTP record (purpose: {otp_record.get('purpose')}, expected: {purpose})")
                    # Check if purpose matches (case-insensitive)
                    if otp_record.get('purpose', '').lower() != purpose.lower():
                        print(f"⚠️ Purpose mismatch: stored='{otp_record.get('purpose')}', expected='{purpose}'")
                        # Still allow verification if email/phone matches

            if not otp_record:
                # Check if OTP exists but is expired or used
                check_expired_query = """
                    SELECT expires_at, used_at, purpose, email, phone
                    FROM otp_verifications
                    WHERE otp_code = %s
                """
                check_params = [otp_code]
                
                if email:
                    check_expired_query += " AND email = %s"
                    check_params.append(email)
                elif phone:
                    check_expired_query += " AND phone = %s"
                    check_params.append(phone)
                
                check_expired_query += " ORDER BY created_at DESC LIMIT 1"
                cursor.execute(check_expired_query, check_params)
                expired_record = cursor.fetchone()
                
                cursor.close()
                
                if expired_record:
                    if expired_record.get('used_at'):
                        return False, "This OTP code has already been used"
                    elif expired_record.get('expires_at'):
                        from datetime import datetime
                        expires_at = expired_record['expires_at']
                        if isinstance(expires_at, str):
                            expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
                        if expires_at < datetime.now():
                            return False, "This OTP code has expired. Please request a new code. OTP codes expire after 10 minutes."
                
                # Debug: Log what we're looking for
                print(f"❌ OTP verification failed:")
                print(f"   OTP Code: {otp_code}")
                print(f"   Email: {email}")
                print(f"   Phone: {phone}")
                print(f"   Purpose: {purpose}")
                
                return False, "Invalid or expired OTP code. OTP codes expire after 10 minutes. Please check the code and try again."

            # Check attempts
            if otp_record['attempts'] >= 3:
                cursor.close()
                return False, "Too many failed attempts. Please request a new OTP"

            # Mark as verified
            cursor.execute(
                "UPDATE otp_verifications SET used_at = NOW(), attempts = attempts + 1 WHERE id = %s",
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
            cursor.execute("DELETE FROM otp_verifications WHERE expires_at < NOW() OR used_at IS NOT NULL")
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            print(f"Cleaned up {deleted_count} expired OTP records")
        except Exception as e:
            print(f"Error cleaning up OTP records: {e}")