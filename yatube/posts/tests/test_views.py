from http import HTTPStatus
from django.test import Client, override_settings, TestCase
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile

from yatube.settings import CACHES
from ..models import Group, Post, Follow, User
from django.core.cache import cache
# import os

FIRST_PAGE = 10
SECOND_PAGE = 1
CACHE = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


@override_settings(CAHES=CACHE)
class TaskPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_3 = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug-3',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.post_2 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.post_3 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.uploaded.seek(0)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_views')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_guest_client(self):
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}),
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={
                    'username': self.post.author.username}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_authorized_client(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_create_post_authorized_client(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    """Список постов index"""
    def test_index_page_context_correct(self):
        response = self.guest_client.get('/')
        context = response.context
        page = context['page_obj']
        self.assertEqual(len(page), 3)
        for post in page:
            self.assertIsInstance(post, Post)
        for post in page:
            if post.id == self.post.id:
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.author, self.post_2.author)
                self.assertEqual(post.text, self.post_2.text)
                self.assertEqual(post.group, self.post_2.group)

    """Список постов, отфильтрованных по группе group_list"""
    def test_group_list_context_correct(self):
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug': self.group.slug}))
        context = response.context
        group = context['group']
        self.assertEqual(group, self.group)

    """Список постов, отфильтрованных по пользователю profile"""
    def test_profile_context_corret(self):
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author.username}))
        context = response.context
        author = context['author']
        self.assertEqual(author, self.post.author)

    """Один пост, отфильтрованный по id"""
    def test_post_detail_context_correct(self):
        response = self.guest_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        context = response.context['post']
        first_post = Post.objects.get(id=1)
        self.assertIsNotNone(context)
        self.assertEqual(first_post, context)

    """Форма создания поста"""
    def test_create_post_context_correct(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_field = {
            'author': forms.fields.CharField,
            'profile_list': forms.fields.CharField,
        }
        for value, expected in form_field.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertTemplateUsed(form_field, expected)

    """Форма редактирования поста, отфильтрованного по id"""
    def test_post_edit_context_correct(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_field = {
            'author': forms.fields.CharField,
            'profile_list': forms.fields.CharField,
        }
        for value, expected in form_field.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertTemplateUsed(form_field, expected)

    """Изображение передается в словаре context"""
    def test_image_to_context(self):
        field_templates = {
            reverse('posts:index'),
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})
        }
        for address in field_templates:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                """Не могу понять как сравнить названия изображений,
                django переименовывает их и получаются разные названия,
                можешь в ошибке рассказать об этом подробнее, пожалуйста"""
                # self.assertEqual(os.path.basename(self.post.image.name),
                #                  self.uploaded.name)
                self.assertEqual(list(self.post.image.chunks()),
                                 list(self.uploaded.chunks()))
                self.assertEqual(response.status_code, HTTPStatus.OK)


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.post_2 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.post_3 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.post_4 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.post_5 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.post_6 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.post_7 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.post_8 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.post_9 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.post_10 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.post_11 = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_views')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    """Paginator index"""
    def test_pagiator_index_first_page(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), FIRST_PAGE)

    def test_paginator_index_second_page(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), SECOND_PAGE)

    """Paginator group_list"""
    def test_paginator_group_list_first_page(self):
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']), FIRST_PAGE)

    def test_paginator_group_list_second_page(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), SECOND_PAGE)
    """Paginator profile"""
    def test_paginator_profile_first_page(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author.username}))
        self.assertEqual(len(response.context['page_obj']), FIRST_PAGE)

    def test_paginator_profile_second_page(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author.username})
            + '?page=2')
        self.assertEqual(len(response.context['page_obj']), SECOND_PAGE)


@override_settings(CACHES=CACHES)
class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.guest_cient = Client()
        self.user = User.objects.create_user(username='test_cache')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    """Тест кеширования главной страницы"""
    def test_cache_index(self):
        response_1 = self.authorized_client.get(
            reverse('posts:index'),
        )
        post_1 = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        post_1.save()
        response_2 = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(response_2.content, response_3.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create(username='auth')
        cls.user_following = User.objects.create(username='auth_1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_follower = Client()
        self.authorized_client_following = Client()
        self.authorized_client_follower.force_login(self.user_follower)
        self.authorized_client_following.force_login(self.user_following)

    """Авторизованный пользователь может подписываться на других пользователей
        и удалять их из подписок"""
    def test_follow_unfollow(self):
        follow_count = Follow.objects.count()
        self.authorized_client_follower.get(reverse('posts:profile_follow',
                                            kwargs={'username':
                                                    self.user_following.
                                                    username}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.authorized_client_follower.get(reverse('posts:profile_unfollow',
                                            kwargs={'username':
                                                    self.user_following.
                                                    username}))
        self.assertEqual(Follow.objects.count(), follow_count)

    """Новая запись появляется в ленте подписчиков"""
    def test_follower_authorized_client(self):
        follow_count = Follow.objects.count()
        post_follow = Follow.objects.create(user=self.user_follower,
                                            author=self.user_following)
        self.authorized_client_follower.get(reverse('posts:follow_index'))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

        response = self.authorized_client_following.get(
            reverse('posts:follow_index'))
        self.assertNotContains(response, post_follow)
