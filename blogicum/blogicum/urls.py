from django.contrib import admin
from django.contrib.auth import views
from django.views.defaults import permission_denied, page_not_found, \
    server_error
from django.views.generic.edit import CreateView
from django.urls import include, path, reverse_lazy

from .forms import CustomUserCreationForm

handler403 = 'pages.views.csrf_failure_handler'
handler404 = 'pages.views.page_not_found_handler'
handler500 = 'pages.views.server_error_handler'

urlpatterns = [
    path('', include('blog.urls', namespace='blog')),
    path('pages/', include('pages.urls', namespace='pages')),
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path('accounts/login/', views.LoginView.as_view(), name='login'),
    path('403csrf/', permission_denied, {'exception': 'PermissionDenied'},
         name='403csrf'),
    path('404/', page_not_found, name='404'),
    path('500/', server_error, name='500'),
    path(
        'auth/registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=CustomUserCreationForm,
            success_url=reverse_lazy('blog:index'),
        ),
        name='registration',
    ),
]
