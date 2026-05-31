from django.contrib import admin
from django.utils.html import format_html
from .models import Speaker, Sermon, SermonCategory, Question, QuestionCategory


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ['name', 'whatsapp_number', 'sermon_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'whatsapp_number']

    def sermon_count(self, obj):
        return obj.sermons.count()
    sermon_count.short_description = 'Sermons'


@admin.register(SermonCategory)
class SermonCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'colored_badge']
    prepopulated_fields = {'slug': ('name',)}

    def colored_badge(self, obj):
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px">{}</span>',
            obj.color, obj.name
        )
    colored_badge.short_description = 'Color'


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    readonly_fields = ['submitted_at', 'status', 'submitter_ip']
    fields = ['question_text', 'status', 'submitted_at', 'admin_notes']


@admin.register(Sermon)
class SermonAdmin(admin.ModelAdmin):
    list_display = ['title', 'speaker', 'sermon_date', 'media_type', 'question_count', 'view_count', 'is_active', 'questions_enabled']
    list_filter = ['media_type', 'is_active', 'questions_enabled', 'speaker', 'category']
    search_fields = ['title', 'scripture_reference', 'speaker__name']
    date_hierarchy = 'sermon_date'
    inlines = [QuestionInline]
    readonly_fields = ['view_count', 'created_at', 'updated_at']

    def question_count(self, obj):
        count = obj.questions.count()
        pending = obj.questions.filter(status='pending').count()
        if pending:
            return format_html('{} <span style="color:orange">({} pending)</span>', count, pending)
        return count
    question_count.short_description = 'Questions'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['short_question', 'sermon', 'status', 'submitted_at', 'retry_count']
    list_filter = ['status', 'submitted_at']
    search_fields = ['question_text', 'sermon__title']
    readonly_fields = ['id', 'submitted_at', 'sent_at', 'submitter_ip', 'whatsapp_message_id', 'wa_send_error']
    actions = ['retry_send']

    def short_question(self, obj):
        return obj.question_text[:80] + '...' if len(obj.question_text) > 80 else obj.question_text
    short_question.short_description = 'Question'

    def retry_send(self, request, queryset):
        from .whatsapp import send_question_to_speaker
        for q in queryset:
            send_question_to_speaker(q)
        self.message_user(request, f"Retried {queryset.count()} questions.")
    retry_send.short_description = "Retry sending via WhatsApp"


@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name']
