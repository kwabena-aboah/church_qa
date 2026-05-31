from django.db import models
from django.utils import timezone
from tinymce.models import HTMLField
import uuid


class Speaker(models.Model):
    name = models.CharField(max_length=200)
    whatsapp_number = models.CharField(
        max_length=20,
        help_text="International format e.g. 233241234567 (no + or spaces)"
    )
    bio = HTMLField(blank=True)
    photo = models.ImageField(upload_to='speakers/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class SermonCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=7, default='#6366f1', help_text="Hex color code")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Sermon Categories"


class Sermon(models.Model):
    MEDIA_TYPES = [
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('text', 'Text/Notes'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    description = HTMLField(blank=True)
    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE, related_name='sermons')
    category = models.ForeignKey(SermonCategory, on_delete=models.SET_NULL, null=True, blank=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='video')
    media_url = models.URLField(blank=True, help_text="YouTube, Google Drive, or direct URL")
    whatsapp_media_id = models.CharField(max_length=200, blank=True, help_text="WhatsApp media ID if from WA")
    scripture_reference = models.CharField(max_length=200, blank=True)
    sermon_date = models.DateField(default=timezone.now)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    questions_enabled = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} – {self.speaker.name}"

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def pending_question_count(self):
        return self.questions.filter(status='pending').count()

    class Meta:
        ordering = ['-sermon_date', '-created_at']


class QuestionCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='❓')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Question Categories"


class Question(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent to Speaker'),
        ('failed', 'Failed to Send'),
        ('answered', 'Answered'),
        ('flagged', 'Flagged'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sermon = models.ForeignKey(Sermon, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    category = models.ForeignKey(QuestionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitter_ip = models.GenericIPAddressField(null=True, blank=True)
    whatsapp_message_id = models.CharField(max_length=200, blank=True)
    wa_send_error = models.TextField(blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Q for '{self.sermon.title}' [{self.status}]"

    class Meta:
        ordering = ['-submitted_at']
