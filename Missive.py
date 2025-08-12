import os
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv()


def send_chat_message(
    text: str,
    conversation_id: str,
    notification_title: str = "New Message from subseven API",
    notification_body: str = "The robot has something to say",
    username: str = "subseven",
    username_icon: str = "avatar:support@subseven.net",
    author_name: str = "subseven",
    author_link: str = "mailto:support@subseven.net",
    author_icon: str = "avatar:support@subseven.net",
    color: str = "#F68A33",
):
    endpoint = "https://public.missiveapp.com/v1/posts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('MISSIVE_API_TOKEN')}",
    }
    payload = {
        "posts": {
            "conversation": conversation_id,
            "notification": {
                "title": notification_title,
                "body": notification_body,
            },
            "username": username,
            "username_icon": username_icon,
            "attachments": [
                {
                    "author_name": author_name,
                    "author_link": author_link,
                    "author_icon": author_icon,
                    "color": color,
                    "text": text,
                    "timestamp": int(datetime.now().timestamp()),
                }
            ],
        }
    }

    try:
        response = httpx.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response
    except Exception as e:
        print(
            f"Message send failed. Status: {e.response.status_code}. Error: {e.response.text}"
        )
        return e.response


# response = send_chat_message(
#     text="i'm an argument!", conversation_id="7f047bb1-7d05-45b6-9656-7b326b912f39"
# )
# print(response.content)
