from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from .forms import CommentForm, PostForm, ProfileForm
from .models import Category, Comment, Post


class IsAuthorMixin:
    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author.pk != request.user.pk:
            return redirect(
                'blog:post_detail', post_id=self.get_object().pk
            )
        return super().dispatch(request, *args, **kwargs)


class PostDetailView(DetailView):
    post_obj = None
    template_name = 'blog/detail.html'
    model = Post
    pk_url_kwarg = 'post_id'
    queryset = Post.objects.select_related('location', 'category', 'author')

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = self.get_object()
        if (
            not self.post_obj.is_published
            or self.post_obj.pub_date > timezone.now()
            or not self.post_obj.category.is_published
        ):
            if self.request.user.pk != self.post_obj.author.pk:
                raise Http404()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.post_obj.comments.select_related('author')
        )
        return context


class PostEditMixin(LoginRequiredMixin):
    template_name = 'blog/create.html'
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'


class PostCreateView(PostEditMixin, CreateView):
    template_name = 'blog/create.html'
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class PostUpdateView(IsAuthorMixin, PostEditMixin, UpdateView):
    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.get_object().pk}
        )


class PostDeleteView(IsAuthorMixin, PostEditMixin, DeleteView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentDeleteView(instance=self.get_object())
        return context

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class PostListMixin(ListView):
    models = Post
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.annotate(
            comment_count=Count('comments')
        ).select_related(
            'category',
            'location',
            'author',
        ).order_by('-pub_date')
        return queryset


class PostListView(PostListMixin):
    template_name = 'blog/index.html'

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            pub_date__lt=timezone.now(),
            is_published=True,
            category__is_published=True
        )
        return queryset


class CategoryListlView(PostListView):
    template_name = 'blog/category.html'
    category = None

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category.objects.filter(is_published=True),
            slug=self.kwargs.get('category_slug'))

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            category__slug=self.category.slug
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileListView(PostListMixin):
    username = None
    template_name = 'blog/profile.html'

    def dispatch(self, request, *args, **kwargs):
        self.username = self.kwargs.get('username')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        username = self.kwargs.get('username')
        queryset = super().get_queryset().filter(
            author__username=username
        )

        if self.request.user.username != username:
            queryset.filter(
                pub_date__lt=timezone.now(),
                is_published=True,
                category__is_published=True
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            get_user_model(), username=self.kwargs.get('username')
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.get_object().username}
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    post_obj = None
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.post_obj.pk}
        )


class CommentMixin:
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.get_object().post.pk}
        )


class CommentUpdateView(
    LoginRequiredMixin, IsAuthorMixin, CommentMixin, UpdateView
):
    pass


class CommentDeleteView(
    LoginRequiredMixin, IsAuthorMixin, CommentMixin, DeleteView
):
    pass
