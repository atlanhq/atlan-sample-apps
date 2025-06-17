import asyncio  
import os
from typing import List, Dict, Any, Optional
from temporalio import activity  
from pyatlan.client.atlan import AtlanClient  
from pyatlan.model.assets import Asset, Table, View, Database
from pyatlan.model.search import IndexSearchRequest
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
from application_sdk.activities import ActivitiesInterface

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed. Please install it with: uv add python-dotenv")
  
class AssetDescriptionReminderActivities(ActivitiesInterface):  
    def __init__(self):  
        # Initialize AtlanClient
        base_url = os.getenv("ATLAN_BASE_URL")
        api_key = os.getenv("ATLAN_API_KEY")
        
        if not base_url or not api_key:
            raise ValueError("Missing required environment variables: ATLAN_BASE_URL and/or ATLAN_API_KEY")
        
        # Create the Atlan client
        self.atlan_client = AtlanClient(base_url=base_url, api_key=api_key)
        AtlanClient.set_current_client(self.atlan_client)
        
        # Initialize Slack client
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            print("Warning: SLACK_BOT_TOKEN not found. Slack functionality will be disabled.")
            self.slack_client = None
        else:
            self.slack_client = WebClient(token=slack_token)
          
    async def _get_atlan_client(self) -> AtlanClient:  
        """Return the initialized Atlan client and set it as current"""  
        AtlanClient.set_current_client(self.atlan_client)
        return self.atlan_client
    
    @activity.defn  
    async def get_tenant_users(self) -> List[Dict[str, Any]]:
        """Get list of users in the tenant by calling the admin API directly."""
        client = await self._get_atlan_client()
        base_url = os.getenv("ATLAN_BASE_URL")
        api_key = client.api_key # Get the api_key from the client instance
        
        if not base_url or not api_key:
            print("❌ ATLAN_BASE_URL or ATLAN_API_KEY not set. Cannot make direct API call.")
            return []
            
        # Use the direct admin API endpoint provided in the curl command
        users_api_url = f"{base_url}/api/service/users"
        
        # Construct headers with the API key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Define parameters to fetch necessary columns
        params = {
            "limit": 100,
            "offset": 0,
            "sort": "firstName",
            "columns": ["firstName", "lastName", "username", "email"]
        }
        
        try:
            print(f"📞 Calling direct Atlan Users API: {users_api_url}")
            
            # Use the requests library to make the authenticated call
            response = requests.get(users_api_url, headers=headers, params=params)
            response.raise_for_status()  # Will raise an exception for 4xx/5xx errors
            
            data = response.json()
            user_records = data.get("records", [])
            
            if not user_records:
                print("⚠️ API call successful, but 0 users returned. Check the API key's permissions.")
                return []
                
            users = []
            for user_data in user_records:
                # Ensure the user has a username before adding
                if "username" in user_data and user_data["username"]:
                    user_info = {
                        "username": user_data.get("username", ""),
                        "email": user_data.get("email", ""),
                        "firstName": user_data.get("firstName", ""),
                        "lastName": user_data.get("lastName", ""),
                        "displayName": f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}".strip()
                    }
                    users.append(user_info)

            print(f"✅ Successfully fetched {len(users)} users from the admin API.")
            return users

        except Exception as e:
            print(f"❌ Failed to fetch users via direct API call: {e}")
            if "403" in str(e) or "Forbidden" in str(e):
                print("      Received a 403 Forbidden error. The API key may be valid but lacks permissions for this endpoint.")
            elif "401" in str(e) or "Unauthorized" in str(e):
                 print("      Received a 401 Unauthorized error. Please check that your ATLAN_API_KEY is correct.")
            
            print("---------------------FALLING BACK TO MOCK DATA--------------------------------")
            return [
                {"username": "mock.user1", "email": "mock.user1@company.com", "firstName": "Mock", "lastName": "User1", "displayName": "Mock User 1"},
                {"username": "mock.user2", "email": "mock.user2@company.com", "firstName": "Mock", "lastName": "User2", "displayName": "Mock User 2"},
            ]
      
    @activity.defn  
    async def fetch_user_assets(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:  
        """Activity 1: Fetch 50 most assets owned by the selected user"""  
        user_username = args["user_username"]
        limit = args.get("limit", 50)
        
        client = await self._get_atlan_client()  
          
        print(f"Fetching assets owned by user: {user_username}")
        
        # Search for assets owned by the specific user
        search_request = IndexSearchRequest(  
            dsl={  
                "query": {  
                    "bool": {  
                        "must": [  
                            {"term": {"__state": "ACTIVE"}},
                            {"terms": {"__typeName.keyword": ["Table", "View", "Database"]}},
                            {"term": {"ownerUsers": user_username}}  # Filter by asset owner
                        ]  
                    }  
                },  
                "from": 0,
                "size": limit,
                "attributes": [  
                    "qualifiedName",  
                    "name",   
                    "description",
                    "ownerUsers",
                    "userDescription"
                ]  
            }  
        )  

        print("search_request", search_request)

        assets_data = []  
          
        try:
            for asset in client.asset.search(search_request):  
                asset_info = {  
                    "qualified_name": getattr(asset.attributes, 'qualified_name', ''),
                    "name": getattr(asset.attributes, 'name', ''),
                    "description": getattr(asset.attributes, 'description', ''),
                    "user_description": getattr(asset.attributes, 'user_description', ''),
                    "owner_users": getattr(asset.attributes, 'owner_users', []),
                    "guid": asset.guid,
                    "type_name": asset.type_name
                }  
                assets_data.append(asset_info)
                print(f"Found asset: {asset_info['name']} - Description: {bool(asset_info['description'] or asset_info['user_description'])}")
        except Exception as e:
            print(f"Error searching for user assets 🫳: {str(e)}")
            # Return mock data for development/testing
            assets_data = [
                {
                    "qualified_name": f"default/database/table_{i}",
                    "name": f"user_table_{i}",
                    "description": "" if i % 3 == 0 else f"Description for table {i}",  # Every 3rd table has no description
                    "user_description": "",
                    "owner_users": [user_username],
                    "guid": f"guid_{i}",
                    "type_name": "Table"
                }
                for i in range(10)  # Return 10 mock assets
            ]
                  
        print(f"Total assets found for {user_username}: {len(assets_data)}")
        return assets_data  
      
    @activity.defn  
    async def find_asset_without_description(self, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:  
        """Activity 2: Check if description of any asset is empty, get the first one"""  
        assets_data = args["assets_data"]
        
        for asset in assets_data:  
            # Check if both description and user_description are empty, handling None values
            description = (asset.get("description") or "").strip()
            user_description = (asset.get("user_description") or "").strip()
            
            if not description and not user_description:
                print(f"Found asset without description: {asset['name']}")
                return asset
                      
        print("All assets have descriptions")
        return None
      
    @activity.defn  
    async def find_slack_user(self, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:  
        """Activity 3: Find the person by email in Slack"""
        # For now, we will use a hardcoded email as requested.
        email_to_find = "adityaework@gmail.com"
        username = args["username"] # We still get this but won't use it for lookup for now.

        if not self.slack_client:
            print("Slack client not available")
            # Return mock data for development/testing
            return {
                "id": "U1234567890",
                "name": username,
                "real_name": username.replace(".", " ").title(),
                "email": email_to_find,
                "display_name": username.replace(".", " ").title()
            }

        try:
            print(f"🔍 Looking for Slack user with email: {email_to_find}")
            # Use the users_lookupByEmail method
            response = self.slack_client.users_lookupByEmail(email=email_to_find)

            user = response.get('user')

            if user:
                print(f"✅ Found Slack user: {user.get('name')} for email: {email_to_find}")
                return {
                    "id": user['id'],
                    "name": user.get('name', ''),
                    "real_name": user.get('real_name', ''),
                    "email": user.get('profile', {}).get('email', ''),
                    "display_name": user.get('profile', {}).get('display_name', '')
                }

            print(f"❌ No matching Slack user found for email: {email_to_find}")
            return None

        except SlackApiError as e:
            print(f"❌ Error searching Slack users by email: {e}")
            if e.response["error"] == "users_not_found":
                print(f"      No user with the email '{email_to_find}' was found in the workspace.")
            elif "not_authed" in str(e):
                print("      The Slack token is invalid or has been revoked.")
            elif "invalid_auth" in str(e):
                print("      Invalid Slack authentication. Check your SLACK_BOT_TOKEN.")
            elif "token_expired" in str(e):
                print("      The Slack token has expired. Please refresh it.")
            return None
      
    @activity.defn  
    async def send_slack_reminder(self, args: Dict[str, Any]) -> Dict[str, Any]:  
        """Activity 4: Send Slack message to the person about missing description"""  
        slack_user = args["slack_user"]
        asset = args["asset"]
        user_username = args["user_username"]
        
        if not self.slack_client:
            print("Slack client not available - would send message")
            return {
                "success": True,
                "message_id": "mock_message_id",
                "message": "Mock message sent (Slack not configured)"
            }
        
        try:
            # Create the reminder message
            message = f"""
Hi {slack_user.get('real_name', slack_user['name'])}! 👋

I noticed that your asset **{asset['name']}** is missing a description. 

Asset Details:
• Name: {asset['name']}
• Type: {asset.get('type_name', 'Asset')}
• Qualified Name: {asset['qualified_name']}

Adding a description helps other team members understand what this asset is used for and makes it easier to discover and use.

Could you please add a description when you get a chance? Thanks! 🙏

_This is an automated reminder from the Asset Description Monitor._
            """
            
            # Send direct message to the user
            response = self.slack_client.chat_postMessage(
                channel=slack_user['id'],  # Send as DM
                text=message.strip(),
                username="Asset Description Monitor",
                icon_emoji=":memo:"
            )
            
            print(f"Slack message sent successfully to {slack_user['name']}")
            return {
                "success": True,
                "message_id": response['ts'],
                "channel": response['channel'],
                "message": "Reminder sent successfully"
            }
            
        except SlackApiError as e:
            print(f"Error sending Slack message: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send reminder"
            } 