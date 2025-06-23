import os
from typing import Any, Dict, List, Optional

from app.clients import AssetDescriptionClient
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from pyatlan.model.search import IndexSearchRequest
from slack_sdk.errors import SlackApiError
from temporalio import activity

logger = get_logger(__name__)


class AssetDescriptionReminderActivities(ActivitiesInterface):
    def __init__(self):
        self.client = None

    async def _get_client(self, config: Dict[str, str]) -> AssetDescriptionClient:
        """Get or create client with config."""
        if not self.client:
            self.client = AssetDescriptionClient()
            await self.client.load(config)
        return self.client

    @activity.defn
    async def fetch_user_assets(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Activity 1: Fetch assets owned by the selected user"""
        client = await self._get_client(args["config"])
        atlan_client = await client.get_atlan_client()
        user_username = args["user_username"]
        limit = args.get("limit", 50)

        logger.info(f"Fetching assets owned by user: {user_username}")

        try:
            search_request = IndexSearchRequest(
                dsl={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"__state": "ACTIVE"}},
                                {
                                    "terms": {
                                        "__typeName.keyword": [
                                            "Table",
                                            "View",
                                            "Database",
                                        ]
                                    }
                                },
                                {"term": {"ownerUsers": user_username}},
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
                        "userDescription",
                    ],
                }
            )

            assets_data = []
            for asset in atlan_client.asset.search(search_request):
                asset_info = {
                    "qualified_name": getattr(asset.attributes, "qualified_name", ""),
                    "name": getattr(asset.attributes, "name", ""),
                    "description": getattr(asset.attributes, "description", ""),
                    "user_description": getattr(
                        asset.attributes, "user_description", ""
                    ),
                    "owner_users": getattr(asset.attributes, "owner_users", []),
                    "guid": asset.guid,
                    "type_name": asset.type_name,
                }
                assets_data.append(asset_info)
                logger.info(
                    f"Found asset: {asset_info['name']} - Description: {bool(asset_info['description'] or asset_info['user_description'])}"
                )
            return assets_data

        except Exception as e:
            logger.error(f"Error searching for user assets: {str(e)}")
            return [{"error": str(e)}]

    @activity.defn
    async def find_asset_without_description(
        self, args: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Activity 2: Check if description of any asset is empty, get the first one"""
        assets_data = args["assets_data"]
        without_description_assets = []
        for asset in assets_data:
            description = (asset.get("description") or "").strip()
            user_description = (asset.get("user_description") or "").strip()
            if not description and not user_description:
                logger.info(f"Found asset without description: {asset['name']}")
                without_description_assets.append(asset)
        
        return {
            "success": True,
            "assets": without_description_assets,
            "count": len(without_description_assets)
        }

    @activity.defn
    async def find_slack_user(self, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Activity 3: Find the person by email in Slack"""
        client = await self._get_client(args["config"])
        slack_client = await client.get_slack_client()
        email_to_find = os.getenv("SLACK_USER_EMAIL")
        username = args["user_username"]

        if not slack_client:
            logger.error("Slack client not available")
            return {"id": "U1234567890", "name": username, "real_name": username}

        try:
            logger.info(f"🔍 Looking for Slack user with email: {email_to_find}")
            response = slack_client.users_lookupByEmail(email=email_to_find)
            user = response.get("user")

            if user:
                return {
                    "id": user["id"],
                    "name": user.get("name"),
                    "real_name": user.get("real_name"),
                    "email": user.get("profile", {}).get("email"),
                    "display_name": user.get("profile", {}).get("display_name"),
                }

            logger.error(f"❌ No matching Slack user found for email: {email_to_find}")
            return None

        except SlackApiError as e:
            logger.error(f"❌ Error searching Slack users by email: {e}")
            if e.response["error"] == "users_not_found":
                logger.error(
                    f"      No user with the email '{email_to_find}' was found in the workspace."
                )
            elif "not_authed" in str(e):
                logger.error("      The Slack token is invalid or has been revoked.")
            elif "invalid_auth" in str(e):
                logger.error(
                    "      Invalid Slack authentication. Check your SLACK_BOT_TOKEN."
                )
            return None

    @activity.defn
    async def send_slack_reminder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Activity 4: Send Slack message to the person about missing description"""
        client = await self._get_client(args["config"])
        slack_client = await client.get_slack_client()
        slack_user = args["slack_user"]
        assets = args["assets"]

        # Format the header
        header = f"Hi {slack_user.get('real_name', slack_user['name'])}! 👋\n\n"
        header += f"I noticed that your {len(assets)} assets are missing a description.\n\n"
        header += "Asset Details:\n"

        # Format each asset's details
        asset_details = []
        for asset in assets:
            asset_text = [
                f"• Name: {asset['name']}",
                f"• Type: {asset.get('type_name', 'Asset')}",
                f"• Qualified Name: {asset['qualified_name']}"
            ]
            asset_details.append("\n".join(asset_text))

        # Format the footer
        footer = "\nAdding a description helps other team members understand what this asset is used for "
        footer += "and makes it easier to discover and use.\n\n"
        footer += "Could you please add a description when you get a chance? Thanks! 🙏\n\n"
        footer += "_This is an automated reminder from the Asset Description Monitor._"

        # Combine all parts
        message = header + "\n\n".join(asset_details) + footer

        if not slack_client:
            logger.error("Slack client not available - would send message")
            return {
                "success": True,
                "message": "Would send message (Slack client not available)",
                "debug": {"user": slack_user, "message": message},
            }

        try:
            response = slack_client.chat_postMessage(
                channel=slack_user["id"],
                text=message.strip(),
                username="Asset Description Monitor",
                icon_emoji=":memo:",
            )
            
            return {
                "success": True,
                "message": "Slack message sent",
                "debug": {"user": slack_user},
            }

        except Exception as e:
            logger.error(f"❌ Error sending Slack message: {e}")
            return {"success": False, "error": str(e)}
