from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json

from sermons.models import Sermon, Question, Speaker, SermonCategory


def _date_range(days):
    end = timezone.now()
    start = end - timedelta(days=days)
    return start, end


@login_required
def dashboard_home(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    # Summary cards
    total_sermons = Sermon.objects.filter(is_active=True).count()
    total_questions = Question.objects.count()
    total_speakers = Speaker.objects.filter(is_active=True).count()
    questions_today = Question.objects.filter(submitted_at__gte=today_start).count()
    questions_week = Question.objects.filter(submitted_at__gte=week_start).count()
    questions_month = Question.objects.filter(submitted_at__gte=month_start).count()
    pending_questions = Question.objects.filter(status='pending').count()
    failed_questions = Question.objects.filter(status='failed').count()
    sent_questions = Question.objects.filter(status='sent').count()
    total_views = sum(Sermon.objects.values_list('view_count', flat=True))

    # Delivery rate
    delivery_rate = round((sent_questions / total_questions * 100) if total_questions else 0, 1)

    # Top sermons by questions
    top_sermons = Sermon.objects.annotate(
        q_count=Count('questions')
    ).filter(is_active=True).order_by('-q_count')[:5]

    # Questions per day (last 14 days)
    q_per_day = (
        Question.objects
        .filter(submitted_at__gte=now - timedelta(days=14))
        .annotate(day=TruncDay('submitted_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    chart_days = [(now - timedelta(days=i)).strftime('%b %d') for i in range(13, -1, -1)]
    day_map = {d['day'].strftime('%b %d'): d['count'] for d in q_per_day}
    chart_values = [day_map.get(d, 0) for d in chart_days]

    # Questions by status
    status_data = list(
        Question.objects.values('status').annotate(count=Count('id')).order_by('-count')
    )

    # Questions by category
    cat_data = list(
        Question.objects.filter(category__isnull=False)
        .values('category__name', 'category__icon')
        .annotate(count=Count('id'))
        .order_by('-count')[:6]
    )

    # Speaker stats
    speaker_stats = (
        Speaker.objects.filter(is_active=True)
        .annotate(
            sermon_count=Count('sermons', filter=Q(sermons__is_active=True)),
            question_count=Count('sermons__questions'),
        )
        .order_by('-question_count')[:8]
    )

    # Recent questions (last 20)
    recent_questions = Question.objects.select_related('sermon__speaker').order_by('-submitted_at')[:20]

    # Engagement: avg questions per sermon
    avg_q_per_sermon = round(
        Question.objects.count() / max(Sermon.objects.filter(is_active=True).count(), 1), 1
    )

    context = {
        # Cards
        'total_sermons': total_sermons,
        'total_questions': total_questions,
        'total_speakers': total_speakers,
        'questions_today': questions_today,
        'questions_week': questions_week,
        'questions_month': questions_month,
        'pending_questions': pending_questions,
        'failed_questions': failed_questions,
        'sent_questions': sent_questions,
        'total_views': total_views,
        'delivery_rate': delivery_rate,
        'avg_q_per_sermon': avg_q_per_sermon,
        # Charts
        'chart_days_json': json.dumps(chart_days),
        'chart_values_json': json.dumps(chart_values),
        'status_data_json': json.dumps(status_data),
        'cat_data_json': json.dumps(cat_data),
        # Tables
        'top_sermons': top_sermons,
        'speaker_stats': speaker_stats,
        'recent_questions': recent_questions,
    }
    return render(request, 'dashboard/home.html', context)


@login_required
def questions_list(request):
    questions = Question.objects.select_related('sermon__speaker', 'category').order_by('-submitted_at')

    status = request.GET.get('status', '')
    if status:
        questions = questions.filter(status=status)

    sermon_id = request.GET.get('sermon', '')
    if sermon_id:
        questions = questions.filter(sermon_id=sermon_id)

    speaker_id = request.GET.get('speaker', '')
    if speaker_id:
        questions = questions.filter(sermon__speaker_id=speaker_id)

    sermons = Sermon.objects.filter(is_active=True).select_related('speaker')
    speakers = Speaker.objects.filter(is_active=True)

    return render(request, 'dashboard/questions.html', {
        'questions': questions[:100],
        'sermons': sermons,
        'speakers': speakers,
        'active_status': status,
        'active_sermon': sermon_id,
        'active_speaker': speaker_id,
    })


@login_required
def api_metrics(request):
    """JSON endpoint for live metric refresh."""
    pending = Question.objects.filter(status='pending').count()
    failed = Question.objects.filter(status='failed').count()
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = Question.objects.filter(submitted_at__gte=today).count()
    return JsonResponse({
        'pending': pending,
        'failed': failed,
        'today': today_count,
        'timestamp': timezone.now().isoformat(),
    })


@login_required
def retry_question(request, pk):
    """Retry sending a failed question."""
    from sermons.models import Question
    from sermons.whatsapp import send_question_to_speaker
    if request.method == 'POST':
        q = Question.objects.get(pk=pk)
        send_question_to_speaker(q)
        return JsonResponse({'success': True, 'status': q.status})
    return JsonResponse({'error': 'POST required'}, status=400)
