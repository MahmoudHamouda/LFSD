import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import get_settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.settings = get_settings()

    def send_email(self, to_email: str, subject: str, html_content: str):
        """
        Send an email using the configured SMTP server.
        """
        if not self.settings.SMTP_SERVER or not self.settings.SMTP_PASSWORD:
            logger.warning("SMTP configuration missing. Email not sent.")
            logger.info(f"Would have sent email to {to_email} with subject: {subject}")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.settings.EMAILS_FROM_NAME} <{self.settings.EMAILS_FROM_EMAIL}>"
            message["To"] = to_email

            part = MIMEText(html_content, "html")
            message.attach(part)

            # Connect to SMTP server
            with smtplib.SMTP(self.settings.SMTP_SERVER, self.settings.SMTP_PORT) as server:
                server.starttls()  # Upgrade connection to secure
                server.login(self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD)
                server.sendmail(
                    self.settings.EMAILS_FROM_EMAIL, to_email, message.as_string()
                )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise e

    def send_password_reset_email(self, to_email: str, token: str):
        """
        Send a password reset email with the link.
        """
        # TODO: Move to a proper frontend URL config
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        
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
        return self.send_email(to_email, subject, html_content)
