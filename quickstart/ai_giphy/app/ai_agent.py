# type: ignore
import os
import smtplib
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

import requests
from application_sdk.observability.logger_adaptor import get_logger
from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

load_dotenv()
logger = get_logger(__name__)

# Default values from environment variables (with defaults where applicable)
_DEFAULT_SMTP_HOST = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
_DEFAULT_SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
_DEFAULT_SMTP_USERNAME = os.getenv("SMTP_USERNAME", "apikey")
_DEFAULT_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
_DEFAULT_SMTP_SENDER = os.getenv("SMTP_SENDER", "support@atlan.app")
_DEFAULT_GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
_DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_DEFAULT_OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-mini")
_DEFAULT_OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")


def _fetch_gif_impl(search_term: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Fetches a random GIF from Giphy API based on the search term.

    Args:
        search_term (str): The search query to find a relevant GIF.
        config (Optional[Dict[str, Any]]): Configuration dictionary with giphy_api_key.

    Returns:
        str: URL of the fetched GIF. Returns a fallback GIF URL if the fetch fails.
    """
    # Priority: config -> env vars -> None
    giphy_api_key = None
    if config:
        giphy_api_key = config.get("giphy_api_key")
    giphy_api_key = giphy_api_key or _DEFAULT_GIPHY_API_KEY

    if not giphy_api_key:
        raise ValueError(
            "GIPHY_API_KEY is not set, please set it in the workflow_args or environment variables for the application. "
            "For reference, please refer to the README.md file and .env.example file."
        )

    url = f"https://api.giphy.com/v1/gifs/random?api_key={giphy_api_key}&tag={search_term}&rating=pg"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        gif_url = data["data"]["images"]["original"]["url"]
        return gif_url
    except Exception as e:
        logger.error(f"Failed to fetch GIF: {e}")
        # Fallback GIF
        return "https://media.giphy.com/media/3o7abAHdYvZdBNnGZq/giphy.gif"


def _send_email_with_gify_impl(
    to: str, gify_url: str, config: Optional[Dict[str, Any]] = None
):
    """
    Send an email to the given recipient with the specified subject and body.

    Args:
        to (str): Recipient email address.
        gify_url (str): URL of the GIF to include.
        config (Optional[Dict[str, Any]]): Configuration dictionary with SMTP settings.
    """
    # Priority: config -> env vars -> defaults
    if config:
        smtp_host = config.get("smtp_host") or _DEFAULT_SMTP_HOST
        smtp_port = config.get("smtp_port")
        if smtp_port is None:
            smtp_port = _DEFAULT_SMTP_PORT
        else:
            smtp_port = int(smtp_port)
        smtp_username = config.get("smtp_username") or _DEFAULT_SMTP_USERNAME
        smtp_password = config.get("smtp_password") or _DEFAULT_SMTP_PASSWORD
        smtp_sender = config.get("smtp_sender") or _DEFAULT_SMTP_SENDER
    else:
        smtp_host = _DEFAULT_SMTP_HOST
        smtp_port = _DEFAULT_SMTP_PORT
        smtp_username = _DEFAULT_SMTP_USERNAME
        smtp_password = _DEFAULT_SMTP_PASSWORD
        smtp_sender = _DEFAULT_SMTP_SENDER

    if not smtp_password:
        raise ValueError(
            "SMTP_PASSWORD is not set, please set it in the workflow_args or environment variables for the application. "
            "For reference, please refer to the README.md file and .env.example file."
        )

    sender = smtp_sender
    subject = "Your Surprise GIF!"
    body = f"""
        <html>
            <body>
                <p>Here's a fun GIF for you!</p>
                <img src="{gify_url}" alt="Random GIF" style="max-width: 500px;">
                <p>Enjoy!</p>
            </body>
        </html>
    """

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)  # pyright: ignore[reportArgumentType]
            server.send_message(msg)
        return "Email sent successfully"
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise


def get_chain(config: Optional[Dict[str, Any]] = None):
    """
    Creates and returns an AI agent chain with tools.

    Args:
        config (Optional[Dict[str, Any]]): Configuration dictionary containing:
            - openai_api_key (str, optional): OpenAI API key (falls back to env var)
            - openai_model_name (str, optional): OpenAI model name (falls back to env var, then default)
            - openai_base_url (str, optional): OpenAI base URL (falls back to env var)
            - giphy_api_key (str, optional): Giphy API key (falls back to env var)
            - smtp_host (str, optional): SMTP host (falls back to env var, then default)
            - smtp_port (int, optional): SMTP port (falls back to env var, then default)
            - smtp_username (str, optional): SMTP username (falls back to env var, then default)
            - smtp_password (str, optional): SMTP password (falls back to env var)
            - smtp_sender (str, optional): SMTP sender email (falls back to env var)

    Returns:
        AgentExecutor: The configured AI agent executor.
    """
    # Priority: config -> env vars -> defaults
    if config:
        openai_api_key = config.get("openai_api_key") or _DEFAULT_OPENAI_API_KEY
        openai_model_name = (
            config.get("openai_model_name") or _DEFAULT_OPENAI_MODEL_NAME
        )
        openai_base_url = config.get("openai_base_url") or _DEFAULT_OPENAI_BASE_URL
    else:
        openai_api_key = _DEFAULT_OPENAI_API_KEY
        openai_model_name = _DEFAULT_OPENAI_MODEL_NAME
        openai_base_url = _DEFAULT_OPENAI_BASE_URL

    if not openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set, please set it in the workflow_args or environment variables for the application."
        )

    local_llm = ChatOpenAI(
        api_key=openai_api_key,
        model=openai_model_name,
        base_url=openai_base_url,  # Passing None is allowed and simply ignored
    )

    # Create closures that capture the config
    def fetch_gif(search_term: str) -> str:
        """
        Fetches a random GIF from Giphy API based on the search term.

        Args:
            search_term (str): The search query to find a relevant GIF.

        Returns:
            str: URL of the fetched GIF. Returns a fallback GIF URL if the fetch fails.
        """
        return _fetch_gif_impl(search_term, config)

    def send_email_with_gify(to: str, gify_url: str):
        """
        Send an email to the given recipient with the specified GIF.

        Args:
            to (str): Recipient email address.
            gify_url (str): URL of the GIF to include in the email.

        Returns:
            str: Success message if email is sent successfully.
        """
        return _send_email_with_gify_impl(to, gify_url, config)

    local_tools = [
        StructuredTool.from_function(fetch_gif),
        StructuredTool.from_function(send_email_with_gify),
    ]

    try:
        prompt = hub.pull("hwchase17/openai-tools-agent")
        agent = create_tool_calling_agent(local_llm, local_tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=local_tools, verbose=True)
        return agent_executor
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise e
