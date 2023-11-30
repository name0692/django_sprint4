from django.conf import settings

from django.conf.urls.static import static
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
                  path('', views.index, name='index'),
                  path('posts/<int:post_id>/', views.post_detail,
                       name='post_detail'),
                  path(
                      'category/<slug:category_slug>/',
                      views.category_posts,
                      name='category_posts'
                  ),
                  path(
                      'posts/create/',
                      views.PostCreateView.as_view(),
                      name='create_post'
                  ),
                  path(
                      'posts/<int:post_id>/edit/',
                      views.edit_post,
                      name='edit_post'
                  ),
                  path(
                      'posts/<int:post_id>/delete/',
                      views.delete_post,
                      name='delete_post'
                  ),
                  path(
                      'posts/<int:post_id>/comment/',
                      views.add_comment,
                      name='add_comment'
                  ),
                  path(
                      'posts/<int:post_id>/edit_comment/<int:comment_id>/',
                      views.edit_comment,
                      name='edit_comment'
                  ),
                  path(
                      'posts/<int:post_id>/delete_comment/<int:comment_id>/',
                      views.delete_comment,
                      name='delete_comment'
                  ),
                  path(
                      'profile/<str:username>/',
                      views.UserProfileView.as_view(),
                      name='profile'
                  ),
                  path(
                      'profile/edit/',
                      views.UserProfileUpdateView.as_view(),
                      name='edit_profile'
                  ),
                  path(
                      'profile/change_password/',
                      views.CustomPasswordChangeView.as_view(),
                      name='change_password'
                  ),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)