from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from .models import Group, Post, User, Follow
from .forms import PostForm, CommentForm


def paginator_get(queryset, request):
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }


def index(request):
    info = 'Последние обновления на сайте'
    title = 'Это главная страница проекта'
    context = {
        'title': title,
        'info': info,
    }
    context.update(paginator_get(Post.objects.all(), request))
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    AMOUNT = 10
    title = 'Записи сообщества'
    info = 'Здесь будет информация о группах проекта Yatube'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:AMOUNT]
    context = {
        'title': title,
        'info': info,
        'group': group,
        'posts': posts,
    }
    context.update(paginator_get(group.posts.all(), request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile_list = Post.objects.filter(author=user)
    count_post = Post.objects.filter(author=user).count()
    following = None
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=user).exists()
    context = {
        'author': user,
        'profile_list': profile_list,
        'count_post': count_post,
        'following': following,
    }
    context.update(paginator_get(user.posts.all(), request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comment = post.comment.all()
    count_post = Post.objects.filter(author=post_id).count()
    context = {
        'post': post,
        'count_post': count_post,
        'form': form,
        'comment': comment,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST,
        files=request.FILES or None,
    )
    if request.method == 'POST':
        if form.is_valid():
            form.instance.author = request.user
            form.save()
            return redirect('posts:profile', request.user)
    else:
        form = PostForm()
        title = 'Новый пост.'
        context = {
            'form': form,
            'title': title,
        }
        return render(request, 'posts/create_post.html', context)
    return render(request, 'posts/create_post.html')


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post,
        )
        form.instance.author = request.user
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post.id)
    else:
        form = PostForm()
        context = {
            'form': form,
            'is_edit': True,
        }

    return render(request, 'posts/create_post.html', context)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'form': form,
    }
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(request, 'posts/post_detail.html', context)


@login_required
def follow_index(request):
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    context = {
        'posts': posts,
    }
    context.update(paginator_get(posts, request))
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', username=author)
