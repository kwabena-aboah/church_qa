from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_question_task(self, question_id):
    """Async task to send a question via WhatsApp."""
    from .models import Question
    from .whatsapp import send_question_to_speaker

    try:
        question = Question.objects.select_related('sermon__speaker').get(id=question_id)
    except Question.DoesNotExist:
        logger.error(f"Question {question_id} not found")
        return

    success, error = send_question_to_speaker(question)
    if not success:
        raise self.retry(exc=Exception(error))


@shared_task
def retry_failed_questions():
    """Periodic task: retry questions that failed to send (max 3 retries)."""
    from .models import Question
    from .whatsapp import send_question_to_speaker

    failed = Question.objects.filter(status='failed', retry_count__lt=3)
    for q in failed:
        send_question_to_speaker(q)
    return f"Retried {failed.count()} questions"
