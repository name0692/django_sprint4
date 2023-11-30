from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotFound
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import UpdateView, CreateView
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import PasswordChangeView

from .forms import (
    PostForm, CommentForm, CustomUserChangeForm, CustomPasswordChangeForm
)
from .models import Post, Category, Comment

DEFAULT_POSTS_COUNT = 5


def get_queryset(query):
    return query.select_related(
        'category',
        'location',
        'author'
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    )


def index(request):
    template = 'blog/index.html'
    all_posts = get_queryset(Post.objects)

    paginator = Paginator(all_posts, 10)
    page = request.GET.get('page')

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'blog/detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(post=post)
    form = CommentForm()

    if (
            post.is_published and
            (post.category.is_published and post.pub_date <= timezone.now())
    ):
        context = {
            'post': post,
            'comments': comments,
            'form': form,
        }
        return render(request, template, context)

    if (
            request.user == post.author and
            (
                    not post.is_published
                    or not post.category.is_published
                    or post.pub_date > timezone.now()
            )
    ):
        context = {
            'post': post,
            'comments': comments,
            'form': form,
        }
        return render(request, template, context)
    else:
        return HttpResponseNotFound(render(request, 'pages/404.html'))


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)

    posts = get_queryset(category.posts)

    paginator = Paginator(posts, 10)
    page = request.GET.get('page')

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'category': category,
        'page_obj': page_obj,
    }

    return render(request, template, context)


class UserProfileView(LoginRequiredMixin, View):
    template_name = 'blog/profile.html'
    posts_per_page = 10

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        posts = Post.objects.filter(author=user).order_by('-pub_date')

        paginator = Paginator(posts, self.posts_per_page)
        page = request.GET.get('page')

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        form = UserChangeForm(instance=user)
        context = {
            'profile': user,
            'page_obj': page_obj,
            'form': form,
            'full_name': user.get_full_name()
        }
        return render(request, self.template_name, context)


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'registration_form.html'
    success_url = reverse_lazy('blog:profile')

    def get_object(self, queryset=None):
        return self.request.user


class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'password_change.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, self.request.user)
        return response


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('blog:profile',
                            username=request.user.username)
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'blog/user.html', {'form': form})


class PostCreateView(LoginRequiredMixin, CreateView):
    template_name = 'blog/create.html'
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.user == post.author:
        if request.method == 'POST' or request.user.has_perm(
                'blog.change_post'):
            form = PostForm(request.POST, instance=post)
            if form.is_valid():
                form.save()
                return redirect('blog:post_detail', post_id=post_id)
        else:
            form = PostForm(instance=post)

        return render(
            request,
            'blog/create.html',
            {'form': form, 'post': post}
        )
    else:
        return redirect('blog:post_detail', post_id=post_id)


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.user == post.author:
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    else:
        return redirect('blog:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if request.user.is_authenticated and request.user == comment.author:
        if request.method == 'POST':
            form = CommentForm(request.POST, instance=comment)
            if form.is_valid():
                form.save()
                return redirect('blog:post_detail', post_id=post_id)
        else:
            form = CommentForm(instance=comment)
        return render(
            request,
            'blog/comment.html',
            {'form': form, 'comment': comment}
        )
    else:
        return HttpResponseNotFound(render(request, 'pages/404.html'))


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if request.user.is_authenticated and request.user == comment.author:
        if request.method == 'POST':
            comment.delete()
            return redirect('blog:post_detail', post_id=post_id)
        else:
            return render(request, 'blog/comment.html', {'comment': comment})
    else:
        return HttpResponseNotFound(render(request, 'pages/404.html'))
