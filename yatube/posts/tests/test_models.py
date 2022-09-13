from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки корректного обрезания текста',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        group_title = group.title
        post = PostModelTest.post
        post_title = post.text[:15]
        expected_str = {
            group: group_title,
            post: post_title
        }
        for model, expected_value in expected_str.items():
            with self.subTest(model=model):
                self.assertEqual(
                    expected_value, str(model)
                )

    def test_models_verbose_name(self):
        post = PostModelTest.post
        group = PostModelTest.group
        post_text = post.text[:15]
        field_verboses = {
            post_text: post.text[:15],
            group.title: 'Тестовая группа',
            group.slug: 'Тестовый слаг',
            group.description: 'Тестовое описание'
        }
        for model, expected_value in field_verboses.items():
            with self.subTest(model=model):
                self.assertEqual(
                    expected_value, str(model)
                )

    def test_help_text(self):
        post = PostModelTest.post
        post_text = post.text[:15]
        field_help_text = {
            post: post_text,
        }
        for model, expected_value in field_help_text.items():
            with self.subTest(model=model):
                self.assertEqual(
                    expected_value, str(model)
                )
