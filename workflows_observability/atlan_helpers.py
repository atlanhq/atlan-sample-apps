from pyatlan.client.atlan import AtlanClient
import os

def get_atlan_client() -> AtlanClient:
    return AtlanClient(
        base_url=os.getenv("ATLAN_BASE_URL"),
        api_key=os.getenv("ATLAN_API_KEY") 
    )