import shutil
import tempfile

from ..forms import PostForm
from ..models import Post, User, Group
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImagePostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            slug='group_test_slug',
            title='Крутая группа',
            description='Описание'
        )
        cls.image_name = 'small.gif'
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=f'posts/{cls.image_name}'
        )
        cls.form = PostForm()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name=cls.image_name,
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.form_data = {
            'text': cls.post.text,
            'image': cls.uploaded,
            'group': cls.group.pk,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=ImagePostFormTests.form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.latest('id')
        self.assertEqual(last_post.text, ImagePostFormTests.form_data['text'])
        self.assertEqual(last_post.group.pk,
                         ImagePostFormTests.form_data['group'])
        self.assertEqual(last_post.image,
                         f'posts/{ImagePostFormTests.image_name}')

    def test_index_correct_posts(self):
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        post_list = response.context.get('page_obj').object_list
        self.assertEqual(len(post_list), True)
        self.assertEqual(post_list[0].image,
                         f'posts/{ImagePostFormTests.image_name}')

    def test_group_correct_posts(self):
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': ImagePostFormTests.group.slug}))
        post_list = response.context.get('page_obj').object_list
        self.assertEqual(len(post_list), True)
        self.assertEqual(post_list[0].id, ImagePostFormTests.post.id)
        self.assertEqual(post_list[0].image,
                         f'posts/{ImagePostFormTests.image_name}')

    def test_profile_correct_posts(self):
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': ImagePostFormTests.user.username}))
        post_list = response.context.get('page_obj').object_list
        self.assertEqual(len(post_list), True)
        self.assertEqual(post_list[0].author.username,
                         ImagePostFormTests.user.username)
        self.assertEqual(post_list[0].author.id, ImagePostFormTests.user.id)
        self.assertEqual(post_list[0].id, ImagePostFormTests.post.id)
        self.assertEqual(post_list[0].image,
                         f'posts/{ImagePostFormTests.image_name}')

    def test_detail_correct_posts(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': ImagePostFormTests.post.pk})
        )
        post = response.context.get('post')
        self.assertEqual(post.author.username,
                         ImagePostFormTests.user.username)
        self.assertEqual(post.author.id, ImagePostFormTests.user.id)
        self.assertEqual(post.id, ImagePostFormTests.post.id)
        self.assertEqual(post.image,
                         f'posts/{ImagePostFormTests.image_name}')

