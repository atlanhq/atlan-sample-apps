class AnaplanUrls:
    AUTH_AUTHENTICATE = "https://auth.anaplan.com/token/authenticate"

    @staticmethod
    def springboard_apps(host: str) -> str:
        return f"https://{host}/a/springboard-definition-service/apps"

    @staticmethod
    def springboard_pages(host: str) -> str:
        return f"https://{host}/a/springboard-definition-service/pages"

    @staticmethod
    def springboard_page_detail(host: str, page_type: str, page_guid: str) -> str:
        return (
            f"https://{host}/a/springboard-definition-service/{page_type}s/{page_guid}"
        )
