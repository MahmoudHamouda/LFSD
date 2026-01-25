import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import core.config
from jinja2 import Environment, FileSystemLoader, select_autoescaper
import logging
import ssl

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.settings = core.config.get_settings()
        
        # Configure Mailgun
        self.base_url = getattr(self.settings, "APP_BASE_URL", "http://localhost:3000")

    def _mask_email(self, email: str) -> str:
        try:
            user, domain = email.split('@')
            masked_user = user[:2] + '*' * 3 if len(user) > 2 else user + '*' 
            return f"{masked_user}@{domain}"
        except:
            return "******"

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """
        Send an email using the configured SMTP server.
        Handles STARTTLS vs SSL and prevents header injection.
        """
        if not self.settings.SMTP_SERVER or not self.settings.SMTP_PASSWORD:
            logger.warning("SMTP configuration missing. Email not sent.")
            logger.info(f"Would have sent email to {to_email} with subject: {subject}")
            return False

        # Validate headers to prevent injection
        to_email = to_email.strip()
        if "\n" in subject or "\r" in subject:
             logger.error("Security Warning: Header injection detected in Subject.")
             return False
        if "\n" in to_email or "\r" in to_email:
             logger.error("Security Warning: Header injection detected in To Email.")
             return False

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = Header(subject, "utf-8")
            from_header_str = f"{self.settings.EMAILS_FROM_NAME} <{self.settings.EMAILS_FROM_EMAIL}>"
            message["From"] = Header(from_header_str, "utf-8")
            message["To"] = Header(to_email, "utf-8")

            # Deliverability Upgrade: Plain text part
            if text_content is None:
                # Naive strip tags if plain text not provided
                import re
                text_content = re.sub('<[^<]+?>', '', html_content)
                
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")
            
            message.attach(text_part)
            message.attach(html_part)

            # Connect to SMTP server
            use_ssl = self.settings.SMTP_USE_SSL or (self.settings.SMTP_PORT == 465)
            context = ssl.create_default_context()

            if use_ssl:
                with smtplib.SMTP_SSL(self.settings.SMTP_SERVER, self.settings.SMTP_PORT, context=context, timeout=10) as server:
                    server.login(self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD)
                    server.sendmail(self.settings.EMAILS_FROM_EMAIL, to_email, message.as_string())
            else:
                 with smtplib.SMTP(self.settings.SMTP_SERVER, self.settings.SMTP_PORT, timeout=10) as server:
                    if self.settings.SMTP_TLS:
                        server.starttls(context=context)
                    server.login(self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD)
                    server.sendmail(self.settings.EMAILS_FROM_EMAIL, to_email, message.as_string())
            
            logger.info(f"Email sent successfully to {self._mask_email(to_email)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {self._mask_email(to_email)}: {e}")
            # Do NOT raise upstream to avoid leaking stack traces or breaking user flow
            return False

    def send_password_reset_email(self, to_email: str, token: str):
        """
        Send a password reset email with the link.
        """
        reset_link = f"{self.base_url}/reset-password?token={token}"
        
        subject = "Reset Your Password"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Password Reset Request</h2>
                    <p>Hello,</p>
                    <p>We received a request to reset your password. If you didn't make this request, you can safely ignore this email.</p>
                    <p>To reset your password, click the button below:</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Reset Password</a>
                    </p>
                    <p>Or verify using this link: <a href="{reset_link}">{reset_link}</a></p>
                    <p>This link will expire in 1 hour.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 12px; color: #666;">If you're having trouble clicking the password reset button, copy and paste usage the URL above into your web browser.</p>
                </div>
            </body>
        </html>
        """
        
        text_content = f"""
        Reset Your Password
        
        Hello,
        
        We received a request to reset your password. If you didn't make this request, you can safely ignore this email.
        
        To reset your password, visit the following link:
        {reset_link}
        
        This link will expire in 1 hour.
        """
        return self.send_email(to_email, subject, html_content, text_content)
