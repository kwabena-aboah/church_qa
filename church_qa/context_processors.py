from django.conf import settings

def church_settings(request):
    return {
        'CHURCH_NAME': settings.CHURCH_NAME,
        'CHURCH_TAGLINE': settings.CHURCH_TAGLINE,
        'CHURCH_LOGO_URL': settings.CHURCH_LOGO_URL,
    }
