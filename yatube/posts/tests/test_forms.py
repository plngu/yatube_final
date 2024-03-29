from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, Follow

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.user1 = User.objects.create_user(username='First user')
        cls.user2 = User.objects.create_user(username='Second user')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.follow = Follow.objects.create(
            author=PostCreateFormTests.user,
            user=PostCreateFormTests.user1,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': 'TestUser'}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        last_post = Post.objects.latest('id')
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.pk, form_data['group'])

    def test_edit_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostCreateFormTests.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCreateFormTests.post.pk}))
        self.assertEqual(Post.objects.count(), post_count)
        last_post = PostCreateFormTests.post
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.pk, form_data['group'])

    def test_create_anon_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.pk,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post_create_namespace = 'posts:post_create'
        auth_login_namespace = 'users:login'
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response,
                             reverse(f'{auth_login_namespace}') + '?next='
                             + reverse(f'{post_create_namespace}'))

    def test_edit_anon_post(self):
        form_data = {
            'text': 'Тестовый текст 1',
            'group': PostCreateFormTests.group.pk,
        }
        kwargs = {'post_id': PostCreateFormTests.post.pk}
        response = self.client.post(
            reverse('posts:post_edit', kwargs=kwargs),
            data=form_data,
            follow=True
        )
        post_edit_namespace = 'posts:post_edit'
        auth_login_namespace = 'users:login'
        last_post = PostCreateFormTests.post
        check_post = self.client.get(
            reverse('posts:post_detail', kwargs=kwargs))
        check_text = check_post.context.get('post').text
        check_group = check_post.context.get('post').group.pk
        self.assertEqual(last_post.text, check_text)
        self.assertEqual(last_post.group.pk, check_group)
        self.assertRedirects(response,
                             reverse(f'{auth_login_namespace}') + '?next='
                             + reverse(f'{post_edit_namespace}',
                                       kwargs=kwargs))

    # Final sprint
    # Test comments
    def test_create_comment(self):
        comments = self.post.comments.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': PostCreateFormTests.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCreateFormTests.post.pk}))
        comment = self.post.comments.all()[0]
        self.assertEqual(self.post.comments.count(), comments + 1)
        self.assertEqual(comment.text, form_data['text'])

    def test_create_anon_comment(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        kwargs = {'post_id': PostCreateFormTests.post.pk}
        response = self.client.post(
            reverse('posts:add_comment',
                    kwargs=kwargs),
            data=form_data,
            follow=True
        )
        post_create_namespace = 'posts:add_comment'
        auth_login_namespace = 'users:login'
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response,
                             reverse(f'{auth_login_namespace}') + '?next='
                             + reverse(f'{post_create_namespace}',
                                       kwargs=kwargs))

    # Test follows
    def test_auth_user_can_follow(self):
        count = Follow.objects.count()
        kwargs = {'username': PostCreateFormTests.user.username}
        response = self.authorized_client.get(reverse('posts:profile_follow',
                                                      kwargs=kwargs))
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs=kwargs))
        self.assertEqual(count, 1)

    def test_auth_user_can_unfollow(self):
        count = Follow.objects.count()
        kwargs = {'username': PostCreateFormTests.user.username}
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs=kwargs)
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs=kwargs))
        PostCreateFormTests.follow.delete()
        self.assertNotEqual(count, Follow.objects.count())

    def test_new_post_is_on_followers_wall(self):
        response = self.authorized_client1.get(reverse('posts:follow_index'))
        this_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(this_post.text, PostCreateFormTests.post.text)

    def test_new_post_is_not_on_unfollowers_wall(self):
        response_unfollow = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        this_post_un = response_unfollow.context.get('page_obj').object_list
        self.assertNotEqual(len(this_post_un), True)
