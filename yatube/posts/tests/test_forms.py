import shutil
import tempfile

from posts.forms import PostForm
from ..models import Group, Post, User, Comment
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
CACHE = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
@override_settings(CACHES=CACHE)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание'
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
        cls.form = PostForm()
        cls.uploaded.seek(0)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_name')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    """Валидная форма создает запись в Post"""
    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': PostFormTest.group.id,
            'image': PostFormTest.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=self.post.text,
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )

    """Изменение поста с post_id в Post"""
    def test_post_edit(self):
        form_data = {
            'text': 'Тестовый пост',
            'post': PostFormTest.post.id,
            'group': PostFormTest.group_2.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
            ).exists()
        )
        self.assertTrue(Post.objects.filter(
            text='Тестовый пост',
            group=PostFormTest.group_2).exists()
        )
        self.assertFalse(Post.objects.filter(
            text='Тестовый пост',
            group=PostFormTest.group).exists()
        )

    """Изменение поста неавторизованным пользователем"""
    def test_post_edit_guest_client(self):
        form_data = {
            'text': 'Тестовый пост',
            'post': PostFormTest.post.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            secure=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    """После успешной отправки комментарий появляется на странице поста"""
    def test_add_comment(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.get(reverse(
            'posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), comments_count + 1)
