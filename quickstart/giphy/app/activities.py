import os
import smtplib
from email.mime.text import MIMEText
from typing import Any, Dict

import requests
from pydantic import BaseModel, Field
from application_sdk.activities import ActivitiesInterface
from application_sdk.decorators.mcp_tool import mcp_tool
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger

GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "apikey")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SENDER = os.getenv("SMTP_SENDER", "support@atlan.app")


class EmailConfig(BaseModel):
    """Configuration for sending email with GIF."""
    recipients: str = Field(description="Comma-separated email addresses (e.g., user1@example.com, user2@example.com)")
    gif_url: str = Field(description="URL of the GIF to include in the email")
    subject: str = Field(default="GIF from Atlan", description="Email subject line")


class GiphyActivities(ActivitiesInterface):
    @activity.defn
    @mcp_tool(description="Fetch random GIF from Giphy API based on search term")
    async def fetch_gif(self, search_term: str) -> str:
        """
        Fetches a random GIF from Giphy API based on the search term.

        Args:
            search_term (str): The search query to find a relevant GIF.

        Returns:
            str: URL of the fetched GIF. Returns a fallback GIF URL if the fetch fails.

        Logs:
            - INFO: When a GIF is successfully fetched
            - ERROR: When GIF fetch fails
        """
        if not GIPHY_API_KEY:
            raise ValueError(
                "GIPHY_API_KEY is not set, please set it in the environment variables for the application. For reference, please refer to the README.md file and .env.example file"
            )

        url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag={search_term}&rating=pg"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            gif_url = data["data"]["images"]["original"]["url"]
            logger.info(f"Fetched GIF: {gif_url}")
            return gif_url
        except Exception as e:
            logger.error(f"Failed to fetch GIF: {e}")
            return "https://media.giphy.com/media/3o7abAHdYvZdBNnGZq/giphy.gif"  # Fallback GIF

    @activity.defn
    @mcp_tool(description="Send HTML email containing a GIF to specified recipients")
    async def send_email(self, config: EmailConfig) -> str:
        """
        Sends an HTML email containing a GIF to specified recipients using SMTP.

        Args:
            config (EmailConfig): Configuration containing recipients, gif_url, and subject

        Returns:
            str: Success message with details of email sent

        Raises:
            smtplib.SMTPException: If email sending fails

        Logs:
            - INFO: When email is sent successfully
            - ERROR: When email sending fails or no valid recipients
        """
        if not SMTP_PASSWORD:
            # fail the activity if the SMTP_PASSWORD is not set
            raise ValueError(
                "SMTP_PASSWORD is not set, please set it in the environment variables for the application. For reference, please refer to the README.md file and .env.example file"
            )

        gif_url = config.gif_url
        recipients = [
            email.strip()
            for email in config.recipients.split(",")
            if email.strip()
        ]

        if not recipients:
            logger.error("No valid recipients provided")
            raise ValueError("No valid recipients provided")

        sender = SMTP_SENDER
        subject = config.subject
        body = f"""
        <html>
            <body>
                <p>Here's a fun GIF for you!</p>
                <img src="{gif_url}" alt="Random GIF" style="max-width: 500px;">
                <p>GIF URL: {gif_url}</p>
                <p>Enjoy!</p>
            </body>
        </html>
        """

        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)

        try:
            logger.info(f"Sending email to {', '.join(recipients)} with GIF: {gif_url}")

            host = SMTP_HOST
            port = SMTP_PORT
            username = SMTP_USERNAME
            password = SMTP_PASSWORD

            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(username, password)  # pyright: ignore[reportArgumentType]
                server.send_message(msg)

            logger.info(f"Email successfully sent to {', '.join(recipients)}")
            return f"Email successfully sent to {', '.join(recipients)} with subject '{subject}'"
        except Exception as e:
            error_msg = f"Email failed to send to {', '.join(recipients)}: {e}"
            logger.error(error_msg)
            return error_msg
