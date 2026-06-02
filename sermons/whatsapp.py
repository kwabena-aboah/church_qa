"""WhatsApp Business Cloud API integration."""
import requests
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_api_url():
    return (
        f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )


def get_headers():
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }


def normalize_phone(phone: str) -> str:
    """Convert phone to WhatsApp-required format (no +, spaces, or dashes)."""
    return ''.join(filter(str.isdigit, phone))


def send_question_to_speaker(question):
    """Send an anonymous question to the sermon speaker via WhatsApp."""

    try:
        sermon = question.sermon
        speaker = sermon.speaker

        if not speaker.whatsapp_number:
            raise ValueError("Speaker has no WhatsApp number")

        phone = normalize_phone(speaker.whatsapp_number)

        message_body = (
            f"🙏 *Anonymous Question for Your Sermon*\n\n"
            f"📖 *Sermon:* {sermon.title}\n"
            f"📅 *Date:* {sermon.sermon_date.strftime('%B %d, %Y')}\n"
        )

        if getattr(sermon, "scripture_reference", None):
            message_body += f"📜 *Scripture:* {sermon.scripture_reference}\n"

        message_body += (
            f"\n💬 *Question:*\n_{question.question_text}_\n\n"
            f"_This question was submitted anonymously via the church Q&A platform._"
        )

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_body,
            }
        }

        response = requests.post(
            get_api_url(),
            headers=get_headers(),
            json=payload,
            timeout=15
        )

        data = response.json()

        # =========================
        # SUCCESS
        # =========================
        if response.status_code == 200 and "messages" in data:
            message_id = data["messages"][0].get("id", "")

            question.status = "sent"
            question.whatsapp_message_id = message_id
            question.sent_at = timezone.now()
            question.save(update_fields=[
                "status",
                "whatsapp_message_id",
                "sent_at"
            ])

            logger.info(f"Question {question.id} sent to {phone}")
            return True, None

        # =========================
        # API ERROR
        # =========================
        error = data.get("error", {})
        error_message = error.get("message", "Unknown WhatsApp API error")

        question.status = "failed"
        question.wa_send_error = error_message
        question.retry_count = (question.retry_count or 0) + 1
        question.save(update_fields=[
            "status",
            "wa_send_error",
            "retry_count"
        ])

        logger.error(f"WhatsApp API error for question {question.id}: {error_message}")
        return False, error_message

    except requests.RequestException as e:
        question.status = "failed"
        question.wa_send_error = str(e)
        question.retry_count = (question.retry_count or 0) + 1
        question.save(update_fields=[
            "status",
            "wa_send_error",
            "retry_count"
        ])

        logger.exception(f"Network error sending question {question.id}")
        return False, str(e)

    except Exception as e:
        logger.exception(f"Unexpected error sending question {question.id}")
        return False, str(e)


def verify_webhook(token, challenge):
    """Verify WhatsApp webhook (Meta requirement)."""
    if token == settings.WHATSAPP_VERIFY_TOKEN:
        return challenge  # MUST be returned raw
    return None