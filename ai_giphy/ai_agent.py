# type: ignore
import json
import os
import smtplib
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.runnables import Runnable
from langchain_core.tools import StructuredTool
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent

load_dotenv()

def fetch_gif(search_term: str) -> str:
    """
    Fetches a random GIF from Giphy API based on the search term.

    Args:
        search_term (str): The search query to find a relevant GIF.

    Returns:
        str: URL of the fetched GIF. Returns a fallback GIF URL if the fetch fails.
    """
    GIPHY_API_KEY = os.environ["GIPHY_API_KEY"]
    url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag={search_term}&rating=pg"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        gif_url = data["data"]["images"]["original"]["url"]
        return gif_url
    except Exception as e:
        print(f"Failed to fetch GIF: {e}")
        return "https://media.giphy.com/media/3o7abAHdYvZdBNnGZq/giphy.gif"

def send_email_with_gify(to: str, gify_url: str):
    """
    Send an email to the given recipient with the specified subject and body
    """
    SMTP_HOST = os.environ["SMTP_HOST"]
    SMTP_PORT = os.environ["SMTP_PORT"]
    SMTP_USERNAME = os.environ["SMTP_USERNAME"]
    SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]

    sender = "support@atlan.app"
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
        host = SMTP_HOST
        port = SMTP_PORT
        username = SMTP_USERNAME
        password = SMTP_PASSWORD
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(username, password)  # pyright: ignore[reportArgumentType]
            server.send_message(msg)
            return "Email sent successfully"
    except Exception as e:
        print(f"Failed to send email: {e}")
        return "Failed to send email"

def get_chain():
    local_llm = AzureChatOpenAI(
        api_key=os.environ["APP_AZURE_OPENAI_API_KEY"],
        api_version=os.environ["APP_AZURE_OPENAI_API_VERSION"],
        azure_endpoint=os.environ["APP_AZURE_OPENAI_ENDPOINT"],
        azure_deployment=os.environ["APP_AZURE_OPENAI_DEPLOYMENT_NAME"],
    )

    local_tools = [
        StructuredTool.from_function(fetch_gif),
        StructuredTool.from_function(send_email_with_gify),
    ]

    prompt = hub.pull("hwchase17/openai-tools-agent")
    agent = create_tool_calling_agent(local_llm, local_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=local_tools, verbose=True)
    return agent_executor

if __name__ == "__main__":
    chain = get_chain()
    print(chain.invoke({
        "input": "Fetch ironman gif and send it to hkay669@gmail.com"
    }))
