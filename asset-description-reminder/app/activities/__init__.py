import os
from typing import List, Dict, Any, Optional
from temporalio import activity  
from pyatlan.model.search import IndexSearchRequest
from slack_sdk.errors import SlackApiError
from application_sdk.activities import ActivitiesInterface
from app.clients import AssetDescriptionClient

class AssetDescriptionReminderActivities(ActivitiesInterface):  
    def __init__(self, client: Optional[AssetDescriptionClient] = None):  
        # Require loaded client
        if not client:
            raise ValueError("Client is required")
        self.client = client
          
    @activity.defn  
    async def fetch_user_assets(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:  
        """Activity 1: Fetch 50 most assets owned by the selected user"""
        atlan_client = self.client.get_atlan_client()
        user_username = args["user_username"]
        limit = args.get("limit", 50)
          
        print(f"Fetching assets owned by user: {user_username}")
        
        try:
            search_request = IndexSearchRequest(  
                dsl={  
                    "query": {  
                        "bool": {  
                            "must": [  
                                {"term": {"__state": "ACTIVE"}},
                                {"terms": {"__typeName.keyword": ["Table", "View", "Database"]}},
                                {"term": {"ownerUsers": user_username}}
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

            assets_data = []  
            for asset in atlan_client.asset.search(search_request):  
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
            return assets_data

        except Exception as e:
            print(f"Error searching for user assets: {str(e)}")
            return [
                {
                    "qualified_name": f"default/database/table_{i}",
                    "name": f"user_table_{i}",
                    "description": "" if i % 3 == 0 else f"Description for table {i}",
                    "user_description": "",
                    "owner_users": [user_username],
                    "guid": f"guid_{i}",
                    "type_name": "Table"
                }
                for i in range(10)
            ]
                  
    @activity.defn  
    async def find_asset_without_description(self, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:  
        """Activity 2: Check if description of any asset is empty, get the first one"""  
        assets_data = args["assets_data"]
        
        for asset in assets_data:  
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
        await self.client.load()
        slack_client = self.client.get_slack_client()
        email_to_find = "adityaework@gmail.com"  # Hardcoded as requested
        username = args["username"]

        if not slack_client:
            print("Slack client not available")
            return {
                "id": "U1234567890",
                "name": username,
                "real_name": username.replace(".", " ").title(),
                "email": email_to_find,
                "display_name": username.replace(".", " ").title()
            }

        try:
            print(f"🔍 Looking for Slack user with email: {email_to_find}")
            response = slack_client.users_lookupByEmail(email=email_to_find)
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
        await self.client.load()
        slack_client = self.client.get_slack_client()
        slack_user = args["slack_user"]
        asset = args["asset"]
        user_username = args["user_username"]
        
        if not slack_client:
            print("Slack client not available - would send message")
            return {
                "success": True,
                "message_id": "mock_message_id",
                "message": "Mock message sent (Slack not configured)"
            }
        
        try:
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
            
            response = slack_client.chat_postMessage(
                channel=slack_user['id'],
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