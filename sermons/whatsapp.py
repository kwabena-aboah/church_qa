"""WhatsApp Business Cloud API integration."""
import requests
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_api_url():
    return (
        f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}"
        f"/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )


def get_headers():
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }


def send_question_to_speaker(question):
    """Send an anonymous question to the sermon speaker via WhatsApp."""
    sermon = question.sermon
    speaker = sermon.speaker
    phone = speaker.whatsapp_number.strip().replace('+', '').replace(' ', '')

    message_body = (
        f"🙏 *Anonymous Question for Your Sermon*\n\n"
        f"📖 *Sermon:* {sermon.title}\n"
        f"📅 *Date:* {sermon.sermon_date.strftime('%B %d, %Y')}\n"
        f"{'📜 *Scripture:* ' + sermon.scripture_reference + chr(10) if sermon.scripture_reference else ''}"
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

    try:
        response = requests.post(
            get_api_url(),
            headers=get_headers(),
            json=payload,
            timeout=15
        )
        data = response.json()

        if response.status_code == 200 and 'messages' in data:
            question.status = 'sent'
            question.whatsapp_message_id = data['messages'][0].get('id', '')
            question.sent_at = timezone.now()
            question.save(update_fields=['status', 'whatsapp_message_id', 'sent_at'])
            logger.info(f"Question {question.id} sent to {phone}")
            return True, None
        else:
            error = data.get('error', {}).get('message', 'Unknown error')
            question.status = 'failed'
            question.wa_send_error = error
            question.retry_count += 1
            question.save(update_fields=['status', 'wa_send_error', 'retry_count'])
            logger.error(f"Failed to send question {question.id}: {error}")
            return False, error

    except requests.RequestException as e:
        question.status = 'failed'
        question.wa_send_error = str(e)
        question.retry_count += 1
        question.save(update_fields=['status', 'wa_send_error', 'retry_count'])
        logger.exception(f"Network error sending question {question.id}")
        return False, str(e)


def verify_webhook(token, challenge):
    """Verify the WhatsApp webhook."""
    if token == settings.WHATSAPP_VERIFY_TOKEN:
        return challenge
    return None
