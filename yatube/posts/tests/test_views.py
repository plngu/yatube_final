from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Post, Group


User = get_user_model()


class PagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='ProphetSunBoy')
        cls.group = Group.objects.create(
            slug='group_test_slug',
            title='Крутая группа',
            description='Описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.user = User.objects.create_user(username='Test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_named_client = Client()
        self.authorized_named_client.force_login(PagesTests.post.author)

    def test_pages_uses_correct_template(self):
        cache.clear()
        templates_pages_names = {
            'posts:index':
                ('posts/index.html', {}),
            'posts:group_list':
                ('posts/group_list.html',
                 {'slug': PagesTests.group.slug}),
            'posts:profile':
                ('posts/profile.html',
                 {'username': PagesTests.user.username}),
            'posts:post_detail':
                ('posts/post_detail.html',
                 {'post_id': PagesTests.post.pk}),
            'posts:post_edit':
                ('posts/create_post.html',
                 {'post_id': PagesTests.post.pk}),
            'posts:post_create':
                ('posts/create_post.html', {})
        }
        for reverse_name, value in templates_pages_names.items():
            template, add_dict = value
            reverse_name = reverse(reverse_name, kwargs=add_dict)
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_post_correct_form(self):
        fields = {'group': forms.fields.ChoiceField,
                  'text': forms.fields.CharField}
        response = self.authorized_client.get(reverse('posts:post_create'))
        for field_name, expected in fields.items():
            with self.subTest(value=field_name):
                form_field = response.context.get('form').fields.get(
                    field_name)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_form(self):
        fields = {'group': forms.fields.ChoiceField,
                  'text': forms.fields.CharField}
        response = self.authorized_named_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PagesTests.post.pk}))
        for field_name, expected in fields.items():
            with self.subTest(value=field_name):
                form_field = response.context.get('form').fields.get(
                    field_name)
                self.assertIsInstance(form_field, expected)

    def test_index_correct_posts(self):
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        post_list = response.context.get('page_obj').object_list
        self.assertEqual(len(post_list), True)

    def test_group_correct_posts(self):
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PagesTests.group.slug}))
        post_list = response.context.get('page_obj').object_list
        self.assertEqual(len(post_list), True)
        self.assertEqual(post_list[0].group.title, PagesTests.group.title)
        self.assertEqual(post_list[0].group.id, PagesTests.group.id)
        self.assertEqual(post_list[0].id, PagesTests.post.id)

    def test_profile_correct_posts(self):
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PagesTests.user.username}))
        post_list = response.context.get('page_obj').object_list
        self.assertEqual(len(post_list), True)
        self.assertEqual(post_list[0].author.username,
                         PagesTests.user.username)
        self.assertEqual(post_list[0].author.id, PagesTests.user.id)
        self.assertEqual(post_list[0].id, PagesTests.post.id)

    # Test 404
    def test_page_not_found_404(self):
        response = self.client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')

    # Test cache
    def test_zcache(self):
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.post.delete()
        response_after_delete = self.client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_after_delete.content)
        cache.clear()
        response_after_clear_cache = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response_after_clear_cache.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            slug='group_test_slug',
            title='Заголовок',
            description='Описание'
        )
        cls.second_page_posts = settings.POSTS_IN_PAGE - 1
        cls.posts_count = settings.POSTS_IN_PAGE + cls.second_page_posts
        for post in range(cls.posts_count):
            Post.objects.create(
                text=f'Тестовый текст {post}',
                author=cls.user,
                group=cls.group
            )

    def test_index_page1_contains_ten_records(self):
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         settings.POSTS_IN_PAGE)

    def test_group_page1_contains_ten_records(self):
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PaginatorViewsTest.group.slug}))
        self.assertEqual(len(response.context['page_obj']),
                         settings.POSTS_IN_PAGE)

    def test_profile_page1_contains_ten_records(self):
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user.username}))
        self.assertEqual(len(response.context['page_obj']),
                         settings.POSTS_IN_PAGE)

    def test_index_page2_contains_three_records(self):
        cache.clear()
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         PaginatorViewsTest.second_page_posts)

    def test_group_page2_contains_three_records(self):
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PaginatorViewsTest.group.slug})
            + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         PaginatorViewsTest.second_page_posts)

    def test_profile_page2_contains_three_records(self):
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user.username})
            + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         PaginatorViewsTest.second_page_posts)


class PostCreateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            slug='group_test_slug',
            title='Новая группа',
            description='Вау'
        )
        cls.group_false = Group.objects.create(
            slug='group_test_slug_false',
            title='Новая группа FALSE',
            description='Не вау'
        )
        cls.sample_text = 'Тестовый текст'
        cls.post = Post.objects.create(
            text=cls.sample_text,
            author=cls.user,
            group=cls.group
        )

    def test_index_page_contains_current_record(self):
        response = self.client.get(reverse('posts:index'))
        first_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(first_post.text, PostCreateTest.sample_text)
        self.assertEqual(first_post.id, PostCreateTest.post.id)

    def test_group_page_contains_current_record(self):
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostCreateTest.group.slug}))
        first_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(first_post.text, PostCreateTest.sample_text)
        self.assertEqual(first_post.id, PostCreateTest.post.id)

    def test_false_group_page_not_contains_current_record(self):
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostCreateTest.group_false.slug}))
        self.assertEqual(len(response.context.get('page_obj').object_list),
                         False)

    def test_profile_page_contains_current_record(self):
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user.username}))
        first_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(first_post.text, PostCreateTest.sample_text)
        self.assertEqual(first_post.id, PostCreateTest.post.id)
