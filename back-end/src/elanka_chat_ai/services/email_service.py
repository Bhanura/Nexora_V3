"""
Email notification service for user data collection.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""
    
    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_username)
        self.enabled = os.getenv("SMTP_ENABLED", "false").lower() == "true"
        
        if not self.enabled:
            logger.warning("Email service is disabled. Set SMTP_ENABLED=true to enable.")
    
    def send_submission_notification(
        self,
        recipient_emails: List[str],
        client_name: str,
        submitted_data: Dict[str, Any],
        session_id: str
    ) -> bool:
        """
        Send email notification about new user data submission.
        
        Args:
            recipient_emails: List of email addresses to notify
            client_name: Name of the client who owns the chatbot
            submitted_data: Dictionary of submitted form data
            session_id: Chat session ID
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email disabled. Would send to: {recipient_emails}")
            return False
        
        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
        if not recipient_emails:
            logger.warning("No recipient emails provided")
            return False
        
        try:
            # Create email content
            subject = f"New User Data Submission - {client_name}"
            
            # Build HTML table of submitted data
            data_rows = ""
            for field_id, value in submitted_data.items():
                data_rows += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{field_id}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{value}</td>
                </tr>
                """
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #333;">New User Data Submission</h2>
                    <p>A visitor has submitted their information through your chatbot.</p>
                    
                    <h3 style="color: #555;">Submission Details:</h3>
                    <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                        <thead>
                            <tr style="background-color: #f2f2f2;">
                                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Field</th>
                                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data_rows}
                        </tbody>
                    </table>
                    
                    <p style="margin-top: 20px; color: #666;">
                        <strong>Session ID:</strong> {session_id}<br>
                        <strong>Submitted At:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                    
                    <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                    <p style="color: #999; font-size: 12px;">
                        This is an automated notification from your eLanka Chat AI chatbot system.
                    </p>
                </body>
            </html>
            """
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = ", ".join(recipient_emails)
            
            # Attach HTML content
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"Email notification sent to {len(recipient_emails)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False

    def send_welcome_email(self, recipient_email: str, client_name: str, temporary_password: str) -> bool:
        """Send a welcome email with a temporary password to a newly created admin user."""
        if not self.enabled:
            logger.info(f"Email disabled. Would send welcome email to: {recipient_email}")
            return False
            
        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False
            
        try:
            subject = "Welcome to eLanka Chat AI - Your Account Details"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #333;">Welcome to eLanka Chat AI!</h2>
                    <p>Hello {client_name},</p>
                    <p>An administrator has created an account for you on the eLanka Chat AI platform.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #0d6efd; margin: 20px 0;">
                        <p style="margin: 0 0 10px 0;"><strong>Your Login Email:</strong> {recipient_email}</p>
                        <p style="margin: 0;"><strong>Temporary Password:</strong> <code style="background-color: #e9ecef; padding: 2px 6px; border-radius: 4px;">{temporary_password}</code></p>
                    </div>
                    
                    <p>Please log in using the temporary password above. We strongly recommend changing your password immediately after logging in.</p>
                    
                    <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                    <p style="color: #999; font-size: 12px;">
                        This is an automated notification from eLanka Chat AI.
                    </p>
                </body>
            </html>
            """
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
                
            logger.info(f"Welcome email sent to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False

    def send_password_reset_email(self, recipient_email: str, otp_code: str) -> bool:
        """Send a password reset email with an OTP."""
        if not self.enabled:
            logger.info(f"Email disabled. Would send OTP {otp_code} to: {recipient_email}")
            return False
            
        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False
            
        try:
            subject = "Password Reset Request - eLanka Chat AI"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #333;">Password Reset Request</h2>
                    <p>We received a request to reset your password for your eLanka Chat AI account.</p>
                    
                    <p>Your password reset code is:</p>
                    <div style="font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #0d6efd; padding: 15px 0;">
                        {otp_code}
                    </div>
                    
                    <p>This code will expire in 15 minutes.</p>
                    <p>If you did not request a password reset, please ignore this email.</p>
                    
                    <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                    <p style="color: #999; font-size: 12px;">
                        This is an automated notification from eLanka Chat AI.
                    </p>
                </body>
            </html>
            """
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
                
            logger.info(f"Password reset OTP sent to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.enabled:
            logger.info("Email service is disabled")
            return False
        
        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            logger.info("SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
