import re
from django import template

register = template.Library()


@register.filter
def youtube_embed_url(url):
    """Convert any YouTube URL to its embed form."""
    if not url:
        return ''
    # youtu.be/ID
    m = re.search(r'youtu\.be/([A-Za-z0-9_-]{11})', url)
    if m:
        return f'https://www.youtube.com/embed/{m.group(1)}'
    # youtube.com/watch?v=ID
    m = re.search(r'[?&]v=([A-Za-z0-9_-]{11})', url)
    if m:
        return f'https://www.youtube.com/embed/{m.group(1)}'
    # already an embed URL
    if 'youtube.com/embed/' in url:
        return url
    return url


@register.filter
def is_youtube(url):
    return bool(url and ('youtube.com' in url or 'youtu.be' in url))
