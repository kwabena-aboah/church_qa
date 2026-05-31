from django.shortcuts import render
from django.utils import timezone


def privacy_policy(request):
    return render(request, 'pages/privacy_policy.html', {
        'effective_date': 'January 1, 2025',
        'last_updated': timezone.now().strftime('%B %d, %Y'),
    })


def terms_of_service(request):
    return render(request, 'pages/terms_of_service.html', {
        'effective_date': 'January 1, 2025',
        'last_updated': timezone.now().strftime('%B %d, %Y'),
    })
