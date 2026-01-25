"""
Email service for sending verification and notification emails.

This module handles all email-related functionality including:
- Email verification emails
- Password reset emails
- SMTP configuration and sending
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from config import settings


def _create_email_html(title: str, message: str, link: str, link_text: str, footer: str) -> str:
    """
    Create HTML email template.

    Args:
        title: Email title/heading
        message: Main message body
        link: URL for the action button
        link_text: Text for the action button
        footer: Footer text

    Returns:
        HTML email string
    """
    return f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
  <h2>{title}</h2>
  <p>{message}</p>
  <p><a href="{link}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">{link_text}</a></p>
  <p style="color: #666; font-size: 12px; margin-top: 20px;">{footer}</p>
</body>
</html>"""


def send_verification_email(to_email: str, username: str, verification_token: str) -> None:
    """
    Send email verification link to user.

    Args:
        to_email: Recipient email address
        username: User's username for personalization
        verification_token: Verification token to include in link

    Note:
        Errors are caught and logged but don't raise exceptions,
        allowing registration to succeed even if email fails.
    """
    try:
        # Build verification URL
        # In production, this would use the actual frontend URL
        frontend_url = "http://localhost:3000"  # TODO: Move to config
        verification_url = f"{frontend_url}/verify-email?token={verification_token}"

        # Create email content
        subject = "Verify Your Email - Personal Blog Assistant"
        html_body = _create_email_html(
            title=f"Hello {username}!",
            message="Please verify your email address by clicking the link below:",
            link=verification_url,
            link_text="Verify Email Address",
            footer="This link will expire in 24 hours. If you didn't create an account, please ignore this email."
        )

        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.email.smtp_from_name} <{settings.email.smtp_from_email}>"
        message["To"] = to_email

        # Attach HTML body
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)

        # Send email via SMTP
        if settings.email.smtp_username and settings.email.smtp_password:
            with smtplib.SMTP(settings.email.smtp_host, settings.email.smtp_port) as server:
                server.starttls()
                server.login(settings.email.smtp_username, settings.email.smtp_password)
                server.send_message(message)

            print(f"✓ Verification email sent to {to_email}")
        else:
            # Development mode: Log verification link instead of sending email
            print("=" * 60)
            print("EMAIL VERIFICATION (Development Mode)")
            print("=" * 60)
            print(f"To: {to_email}")
            print(f"Username: {username}")
            print(f"Verification URL: {verification_url}")
            print("=" * 60)

    except Exception as e:
        # Log error but don't raise - registration should succeed even if email fails
        print(f"✗ Failed to send verification email to {to_email}: {str(e)}")


def send_password_reset_email(to_email: str, username: str, reset_token: str) -> None:
    """
    Send password reset token to user.

    In development mode, this prints the token to console instead of sending email.
    In production mode (when SMTP credentials are configured), it sends an email.

    Args:
        to_email: Recipient email address
        username: User's username for personalization
        reset_token: Password reset token
    """
    # Development mode: Print token to console
    print("=" * 60)
    print("PASSWORD RESET TOKEN")
    print("=" * 60)
    print(f"User: {username}")
    print(f"Email: {to_email}")
    print(f"Token: {reset_token}")
    print("")
    print("Use this token to reset your password via:")
    print("POST /api/users/reset-password")
    print("")
    print("This token expires in 1 hour.")
    print("=" * 60)

    # Production mode: Send email (if SMTP is configured)
    if settings.email.smtp_username and settings.email.smtp_password:
        try:
            # Build reset URL
            frontend_url = "http://localhost:3000"  # TODO: Move to config
            reset_url = f"{frontend_url}/reset-password?token={reset_token}"

            # Create email content
            subject = "Password Reset Request - Personal Blog Assistant"
            html_body = _create_email_html(
                title=f"Hello {username}!",
                message="You requested to reset your password. Click the link below to reset it:",
                link=reset_url,
                link_text="Reset Password",
                footer="This link will expire in 1 hour. If you didn't request a password reset, please ignore this email."
            )

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.email.smtp_from_name} <{settings.email.smtp_from_email}>"
            message["To"] = to_email

            # Attach HTML body
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

            # Send email via SMTP
            with smtplib.SMTP(settings.email.smtp_host, settings.email.smtp_port) as server:
                server.starttls()
                server.login(settings.email.smtp_username, settings.email.smtp_password)
                server.send_message(message)

            print(f"✓ Password reset email sent to {to_email}")

        except Exception as e:
            print(f"✗ Failed to send password reset email to {to_email}: {str(e)}")
