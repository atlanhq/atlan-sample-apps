import os
import smtplib
from email.mime.text import MIMEText
from typing import Any, Dict

import requests
from application_sdk.activities import ActivitiesInterface
from application_sdk.common.logger_adaptors import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger

GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "apikey")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SENDER = os.getenv("SMTP_SENDER", "support@atlan.app")


class GiphyActivities(ActivitiesInterface):
    @activity.defn
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
        url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag={search_term}&rating=pg"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            gif_url = data["data"]["images"]["original"]["url"]
            activity.logger.info(f"Fetched GIF: {gif_url}")
            return gif_url
        except Exception as e:
            activity.logger.error(f"Failed to fetch GIF: {e}")
            return "https://media.giphy.com/media/3o7abAHdYvZdBNnGZq/giphy.gif"  # Fallback GIF

    @activity.defn
    async def send_email(self, config: Dict[str, Any]) -> None:
        """
        Sends an HTML email containing a GIF to specified recipients using SMTP.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - gif_url (str): URL of the GIF to be sent
                - recipients (str): Comma-separated string of email addresses

        Returns:
            str: Error message if no valid recipients, None otherwise

        Raises:
            smtplib.SMTPException: If email sending fails

        Logs:
            - INFO: When email is sent successfully
            - ERROR: When email sending fails or no valid recipients
        """
        gif_url = config.get("gif_url")
        recipients = [
            email.strip()
            for email in config.get("recipients", "").split(",")
            if email.strip()
        ]

        if not recipients:
            activity.logger.error("No valid recipients provided")
            raise ValueError("No valid recipients provided")

        sender = "support@atlan.app"
        subject = "Your Surprise GIF!"
        body = f"""
        <html>
            <body>
                <p>Here's a fun GIF for you!</p>
                <img src="{gif_url}" alt="Random GIF" style="max-width: 500px;">
                <p>Enjoy!</p>
            </body>
        </html>
        """

        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)

        try:
            activity.logger.info(
                f"Sending email to {', '.join(recipients)} with GIF: {gif_url}"
            )

            host = SMTP_HOST
            port = SMTP_PORT
            username = SMTP_USERNAME
            password = SMTP_PASSWORD

            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(username, password)  # pyright: ignore[reportArgumentType]
                server.send_message(msg)

            activity.logger.info(f"Email successfully sent to {', '.join(recipients)}")
        except Exception as e:
            activity.logger.error(
                f"Email failed to send to {', '.join(recipients)}: {e}"
            )
