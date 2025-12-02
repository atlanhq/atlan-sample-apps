import os
import smtplib
from email.mime.text import MIMEText
from typing import Any, Dict

import requests
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger

# Default values from environment variables (with defaults where applicable)
_DEFAULT_SMTP_HOST = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
_DEFAULT_SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
_DEFAULT_SMTP_USERNAME = os.getenv("SMTP_USERNAME", "apikey")
_DEFAULT_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
_DEFAULT_SMTP_SENDER = os.getenv("SMTP_SENDER")
_DEFAULT_GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")


class GiphyActivities(ActivitiesInterface):
    @activity.defn
    async def fetch_gif(self, config: Dict[str, Any]) -> str:
        """
        Fetches a random GIF from Giphy API based on the search term.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - search_term (str): The search query to find a relevant GIF
                - giphy_api_key (str, optional): Giphy API key (falls back to env var)

        Returns:
            str: URL of the fetched GIF. Returns a fallback GIF URL if the fetch fails.

        Logs:
            - INFO: When a GIF is successfully fetched
            - ERROR: When GIF fetch fails
        """
        # Priority: workflow_args -> env vars -> None
        search_term = config.get("search_term", "funny cat")
        giphy_api_key = config.get("giphy_api_key") or _DEFAULT_GIPHY_API_KEY

        if not giphy_api_key:
            raise ValueError(
                "GIPHY_API_KEY is not set, please set it in the workflow_args or environment variables for the application. For reference, please refer to the README.md file and .env.example file"
            )

        url = f"https://api.giphy.com/v1/gifs/random?api_key={giphy_api_key}&tag={search_term}&rating=pg"
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
    async def send_email(self, config: Dict[str, Any]) -> None:
        """
        Sends an HTML email containing a GIF to specified recipients using SMTP.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - gif_url (str): URL of the GIF to be sent
                - recipients (str): Comma-separated string of email addresses
                - smtp_host (str, optional): SMTP host (falls back to env var, then default)
                - smtp_port (int, optional): SMTP port (falls back to env var, then default)
                - smtp_username (str, optional): SMTP username (falls back to env var, then default)
                - smtp_password (str, optional): SMTP password (falls back to env var)
                - smtp_sender (str, optional): SMTP sender email (falls back to env var)

        Returns:
            None

        Raises:
            ValueError: If no valid recipients or SMTP_PASSWORD is not set
            smtplib.SMTPException: If email sending fails

        Logs:
            - INFO: When email is sent successfully
            - ERROR: When email sending fails or no valid recipients
        """
        # Priority: workflow_args -> env vars -> defaults
        smtp_host = config.get("smtp_host") or _DEFAULT_SMTP_HOST
        smtp_port = config.get("smtp_port")
        if smtp_port is None:
            smtp_port = _DEFAULT_SMTP_PORT
        else:
            smtp_port = int(smtp_port)
        smtp_username = config.get("smtp_username") or _DEFAULT_SMTP_USERNAME
        smtp_password = config.get("smtp_password") or _DEFAULT_SMTP_PASSWORD
        smtp_sender = config.get("smtp_sender") or _DEFAULT_SMTP_SENDER

        if not smtp_password:
            # fail the activity if the SMTP_PASSWORD is not set
            raise ValueError(
                "SMTP_PASSWORD is not set, please set it in the workflow_args or environment variables for the application. For reference, please refer to the README.md file and .env.example file"
            )

        gif_url = config.get("gif_url")
        recipients = [
            email.strip()
            for email in config.get("recipients", "").split(",")
            if email.strip()
        ]

        if not recipients:
            logger.error("No valid recipients provided")
            raise ValueError("No valid recipients provided")

        sender = smtp_sender
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
            logger.info(f"Sending email to {', '.join(recipients)} with GIF: {gif_url}")

            host = smtp_host
            port = smtp_port
            username = smtp_username
            password = smtp_password

            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(username, password)  # pyright: ignore[reportArgumentType]
                server.send_message(msg)

            logger.info(f"Email successfully sent to {', '.join(recipients)}")
        except Exception as e:
            logger.error(f"Email failed to send to {', '.join(recipients)}: {e}")
            raise  # Re-raise the exception so the activity fails
