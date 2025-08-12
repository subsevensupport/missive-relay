import logging
import os
from typing import List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel

import Missive

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Attachment(BaseModel):
    id: str
    filename: str
    extension: str
    url: str
    media_type: str
    sub_type: str
    size: int


class LatestMessage(BaseModel):
    type: str
    attachments: List[Attachment]


class Conversation(BaseModel):
    id: str
    messages_count: int
    attachments_count: int


class MissiveWebhook(BaseModel):
    conversation: Conversation
    latest_message: Optional[LatestMessage] = None


load_dotenv()

app = FastAPI()


async def send_for_transcription(attachment: Attachment, conversation_id: str):
    logger.info(f"Background task started for {attachment.id}")

    beam_endpoint_url = "https://audio-transcriber-cb0e410-v16.app.beam.cloud"
    headers = {
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('BEAM_AUTH_TOKEN')}",
    }
    data = {
        "audio_file_url": attachment.url,
        "callback_data": {"conversation_id": conversation_id},
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(beam_endpoint_url, headers=headers, json=data)
            response.raise_for_status()
            logger.info(
                f"Successfully sent attachment {attachment.id} for transcription. "
                f"Response: {response.content}"
            )
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to send attachment {attachment.id}. "
            f"Status code: {e.response.status_code}. Response: {e.response.text}"
        )
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while sending attachment {attachment.id}: {e}"
        )


@app.post("/transcribe", status_code=status.HTTP_202_ACCEPTED)
async def process_missive_transcription_webhook(
    payload: MissiveWebhook, background_tasks: BackgroundTasks
) -> dict:
    logger.info("Webhook received. Validating payload...")

    latest_message = payload.latest_message
    if not latest_message:
        logger.error("No latest message found in payload")
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No message found. Nothing to process.",
        )

    attachments = latest_message.attachments
    if not attachments:
        logger.error("No attachments found on latest message")
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No attachments found on latest message. Nothing to process.",
        )

    audio_attachments = [a for a in attachments if a.media_type == "audio"]

    if not audio_attachments:
        logger.error("No audio attachments found in the message")
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No audio attachments found. Nothing to transcribe.",
        )

    logger.info(
        f"{len(audio_attachments)} audio attachment(s) found. Sending for transcription..."
    )

    for attachment in audio_attachments:
        background_tasks.add_task(
            send_for_transcription,
            attachment=attachment,
            conversation_id=payload.conversation.id,
        )

    return {
        "status": "success",
        "message": f"Found {len(audio_attachments)} audio attachments. Sent for transcription.",
    }


@app.post("/transcribe-callback")
def process_transcribe_callback_webhook(payload: dict):
    text = payload.get("data").get("transcription_text")
    conversation_id = payload.get("data").get("callback_data").get("conversation_id")
    Missive.send_chat_message(
        text=text,
        conversation_id=conversation_id,
        notification_title="Transcription completed",
        notification_body=text,
        author_name="subseven transcription robot",
    )
