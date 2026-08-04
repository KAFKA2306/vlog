import json
from urllib.request import Request, urlopen

from src.infrastructure.settings import settings


class DiscordClient:
    def send_message(self, message: str) -> None:
        if not settings.discord_webhook_url:
            return

        payload = {"content": message}
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            settings.discord_webhook_url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "VLog-Bot"},
            method="POST",
        )
        with urlopen(request) as response:
            if response.status != 204 and response.status != 200:
                print(f"Failed to send Discord notification: {response.status}")
