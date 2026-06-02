from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.views import View
from django.db.models import Q
from django.core.cache import cache
import json
import logging

from .models import Sermon, Question, SermonCategory, QuestionCategory
from .whatsapp import verify_webhook

logger = logging.getLogger(__name__)

RATE_LIMIT_PER_HOUR = 5  # questions per IP per hour

VERIFY_TOKEN = settings.WHATSAPP_VERIFY_TOKEN


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def check_rate_limit(ip):
    """Return True if under the rate limit."""
    key = f"rl_question_{ip}"
    count = cache.get(key, 0)
    if count >= RATE_LIMIT_PER_HOUR:
        return False
    cache.set(key, count + 1, 3600)
    return True


def sermon_list(request):
    """Public sermon listing page."""
    sermons = Sermon.objects.filter(is_active=True).select_related('speaker', 'category')

    # Search
    q = request.GET.get('q', '')
    if q:
        sermons = sermons.filter(
            Q(title__icontains=q) | Q(speaker__name__icontains=q) |
            Q(scripture_reference__icontains=q)
        )

    # Filter by category
    cat = request.GET.get('category', '')
    if cat:
        sermons = sermons.filter(category__slug=cat)

    # Filter by type
    mtype = request.GET.get('type', '')
    if mtype:
        sermons = sermons.filter(media_type=mtype)

    categories = SermonCategory.objects.all()
    return render(request, 'sermons/list.html', {
        'sermons': sermons,
        'categories': categories,
        'search_query': q,
        'active_cat': cat,
        'active_type': mtype,
    })


def sermon_detail(request, pk):
    """Single sermon page with question form."""
    sermon = get_object_or_404(Sermon, pk=pk, is_active=True)
    # Increment view count (debounced by IP)
    ip = get_client_ip(request)
    view_key = f"view_{pk}_{ip}"
    if not cache.get(view_key):
        Sermon.objects.filter(pk=pk).update(view_count=sermon.view_count + 1)
        cache.set(view_key, 1, 3600)

    question_categories = QuestionCategory.objects.all()
    return render(request, 'sermons/detail.html', {
        'sermon': sermon,
        'question_categories': question_categories,
    })


@require_POST
def submit_question(request, pk):
    """API endpoint to submit a question."""
    sermon = get_object_or_404(Sermon, pk=pk, is_active=True, questions_enabled=True)
    ip = get_client_ip(request)

    if not check_rate_limit(ip):
        return JsonResponse({'error': 'Too many questions. Please wait before submitting again.'}, status=429)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        data = request.POST

    text = (data.get('question_text') or '').strip()
    if not text:
        return JsonResponse({'error': 'Question cannot be empty.'}, status=400)
    if len(text) > 1000:
        return JsonResponse({'error': 'Question is too long (max 1000 characters).'}, status=400)
    if len(text) < 10:
        return JsonResponse({'error': 'Question is too short.'}, status=400)

    cat_id = data.get('category')
    category = None
    if cat_id:
        try:
            category = QuestionCategory.objects.get(id=cat_id)
        except QuestionCategory.DoesNotExist:
            pass

    question = Question.objects.create(
        sermon=sermon,
        question_text=text,
        category=category,
        submitter_ip=ip,
        status='pending',
    )

    # Send via Celery (async) or synchronously if no broker
    try:
        from .tasks import send_question_task
        send_question_task.delay(str(question.id))
    except Exception:
        # Fallback: send synchronously
        from .whatsapp import send_question_to_speaker
        send_question_to_speaker(question)

    return JsonResponse({
        'success': True,
        'message': 'Your question has been submitted anonymously. 🙏',
        'question_id': str(question.id),
    })


@csrf_exempt
def whatsapp_webhook(request):

    # =========================
    # FACEBOOK / WHATSAPP VERIFICATION (GET)
    # =========================
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return HttpResponse(challenge)  # MUST return raw text

        return HttpResponse("Forbidden", status=403)

    # =========================
    # WEBHOOK EVENTS (POST)
    # =========================
    if request.method == "POST":
        try:
            data = request.body.decode("utf-8")
            logger.info(f"WhatsApp webhook received: {data[:500]}")

            # TODO: parse JSON and process messages here

            return JsonResponse({"status": "ok"})

        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            return JsonResponse({"error": "bad request"}, status=400)

    return HttpResponse("Method not allowed", status=405)