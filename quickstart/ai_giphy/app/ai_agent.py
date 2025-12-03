# type: ignore
import os
import smtplib
from email.mime.text import MIMEText

import requests
from application_sdk.observability.logger_adaptor import get_logger
from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

load_dotenv()
logger = get_logger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "apikey")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SENDER = os.getenv("SMTP_SENDER", "support@atlan.app")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")


def fetch_gif(search_term: str) -> str:
    """
    Fetches a random GIF from Giphy API based on the search term.

    Args:
        search_term (str): The search query to find a relevant GIF.

    Returns:
        str: URL of the fetched GIF. Returns a fallback GIF URL if the fetch fails.
    """
    if not GIPHY_API_KEY:
        raise ValueError(
            "GIPHY_API_KEY is not set, please set it in the environment variables for the application. "
            "For reference, please refer to the README.md file and .env.example file."
        )

    url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag={search_term}&rating=pg"
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


def send_email_with_gify(to: str, gify_url: str):
    """
    Send an email to the given recipient with the specified subject and body.
    """
    if not SMTP_PASSWORD:
        raise ValueError(
            "SMTP_PASSWORD is not set, please set it in the environment variables for the application. "
            "For reference, please refer to the README.md file and .env.example file."
        )

    sender = SMTP_SENDER
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
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)  # pyright: ignore[reportArgumentType]
            server.send_message(msg)
        return "Email sent successfully"
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return "Failed to send email"


def get_chain():
    # Only API key is required. Base URL is optional.
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY is not set, please set it in the environment variables for the application."
        )

    # Optional: Only used if someone is using a proxy / Azure / custom gateway
    openai_base_url = os.getenv("OPENAI_BASE_URL", None)

    local_llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL_NAME,
        base_url=openai_base_url,  # Passing None is allowed and simply ignored
    )

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
