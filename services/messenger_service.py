# services/messenger_service.py
import requests
import logging
import time

logger = logging.getLogger("MessengerService")
GRAPH_API_URL = "https://graph.facebook.com/v19.0/me/messages"

def send_messenger_text(recipient_id: str, text: str, page_access_token: str):
    if not page_access_token:
        logger.warning(f"No Page Access Token! Outputting simulated reply to recipient: {recipient_id}")
        logger.info(f"\n--- [SIMULATED REPLY TO {recipient_id}] ---\n{text}\n----------------------------------")
        return

    chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
    logger.info(f"Sending message to recipient {recipient_id} | Total chunks: {len(chunks)}")

    for idx, chunk in enumerate(chunks, start=1):
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": chunk}
        }
        params = {"access_token": page_access_token}
        try:
            res = requests.post(GRAPH_API_URL, params=params, json=payload, timeout=15)
            res.raise_for_status()
            logger.info(f"Chunk {idx}/{len(chunks)} sent successfully to {recipient_id}")
            time.sleep(0.4)
        except Exception as e:
            logger.error(f"Failed to send chunk {idx} to {recipient_id}: {e}")

def download_attachment_bytes(attachment_url: str) -> bytes:
    logger.info(f"Downloading attachment from Meta: {attachment_url[:60]}...")
    res = requests.get(attachment_url, timeout=30)
    res.raise_for_status()
    logger.info(f"Download complete | Attachment size: {len(res.content)} bytes")
    return res.content