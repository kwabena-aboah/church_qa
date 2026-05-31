from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'))),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('', include('sermons.urls')),
    path('', include('pages.urls')),
    path('', include('sermons.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
