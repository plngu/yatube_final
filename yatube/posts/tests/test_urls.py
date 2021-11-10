from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_tech_and_about(self):
        about_pages = {'/about/author/',
                       '/about/tech/'}
        for address in about_pages:
            with self.subTest(field=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            pub_date='Тестовая дата'
        )
        cls.group = Group.objects.create(
            slug='group_test_slug',
            title='Заголовок',
            description='Описание'
        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_named_client = Client()
        self.authorized_named_client.force_login(TaskURLTests.post.author)

    def test_urls_uses_correct_template(self):
        cache.clear()
        templates_url_names = {
            '/':
                ('posts/index.html', self.client),
            f'/group/{TaskURLTests.group.slug}/':
                ('posts/group_list.html', self.client),
            f'/profile/{TaskURLTests.user.username}/':
                ('posts/profile.html', self.client),
            f'/posts/{TaskURLTests.post.pk}/':
                ('posts/post_detail.html', self.client),
            f'/posts/{TaskURLTests.post.pk}/edit/':
                ('posts/create_post.html', self.authorized_named_client),
            '/create/':
                ('posts/create_post.html', self.authorized_client),
            '/unexisting_page/':
                ('', self.client),
        }
        for address, value in templates_url_names.items():
            template, authorization = value
            response = authorization.get(address)
            if not template:
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                continue
            with self.subTest(address=address):
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)
