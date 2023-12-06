from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponseNotFound
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserChangeForm

from .forms import PostForm, CommentForm
from .models import Post, Category, Comment

DEFAULT_POSTS_COUNT = 5
POSTS_PER_PAGE = 10


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
    all_posts = get_queryset(
        Post.objects.annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    )

    paginator = Paginator(all_posts, POSTS_PER_PAGE)
    page = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page)
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

    if post.author != request.user and (
            not post.is_published
            or not post.category.is_published
            or post.pub_date > timezone.now()
    ):
        return HttpResponseNotFound(render(request, 'pages/404.html'))

    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    posts = get_queryset(category.posts)

    paginator = Paginator(posts, POSTS_PER_PAGE)
    page = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'category': category,
        'page_obj': page_obj,
    }

    return render(request, template, context)


class UserProfileDetailView(DetailView):
    template_name = 'blog/profile.html'

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        posts = Post.objects.filter(author=user).annotate(
            comment_count=Count('comments')).order_by('-pub_date')

        paginator = Paginator(posts, POSTS_PER_PAGE)
        page = request.GET.get('page', 1)

        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        context = {
            'profile': user,
            'page_obj': page_obj,
        }
        return render(request, self.template_name, context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = UserChangeForm(instance=request.user)

    return render(request, 'blog/edit_profile.html', {'form': form})


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
