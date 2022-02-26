import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Follow, Group, Post
from ..views import POSTS_NUMBER

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        for i in range(1, 14):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'{i} Тестовый пост',
                group=cls.group,
            )

    def setUp(self):
        self.second_page = Post.objects.count() % POSTS_NUMBER
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_number = {
            reverse('posts:index'): POSTS_NUMBER,
            reverse('posts:index') + '?page=2': self.second_page,
            reverse(
                'posts:group_list', kwargs={'slug': 'testslug'}
            ): POSTS_NUMBER,
            reverse(
                'posts:group_list', kwargs={'slug': 'testslug'}
            ) + '?page=2': self.second_page,
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): POSTS_NUMBER,
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ) + '?page=2': self.second_page
        }

        for reverse_name, page_number in templates_page_number.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), page_number)


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Текст комментария'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        test_object = response.context['page_obj'][0]
        self.assertEqual(test_object, self.post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            )
        )
        test_object = response.context['group']
        test_text = response.context['page_obj'][0].text
        test_group = response.context['page_obj'][0].group.title
        self.assertEqual(test_object, self.group)
        self.assertEqual(test_text, 'Тестовый текст')
        self.assertEqual(test_group, 'Тестовая группа')

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        test_author = response.context['author']
        self.assertEqual(test_author, self.post.author)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        )
        post = response.context['post']
        author = self.post.author
        group = self.group
        text = 'Тестовый текст'
        post_count_user = response.context['post_count_user']
        self.assertEqual(author, post.author)
        self.assertEqual(text, post.text)
        self.assertEqual(group, post.group)
        self.assertEqual(1, post_count_user)

    def test_post_edit_correct_context(self):
        """Шаблон post_create редактирует пост с правильным id"""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_field_text = response.context['form'].initial['text']
        self.assertEqual(form_field_text, self.post.text)

    def test_create_post_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_field_text = response.context['form']
        self.assertIsInstance(form_field_text, PostForm)

    def comment_on_post_detail(self):
        """Комментарий появляется на странице поста"""
        response = self.client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertIn(self.comment, response.context['comments'])

    def test_guest_client_no_comment(self):
        """Неавторизированный пользователь не может комментировать посты"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария',
        }
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_cache_index_page(self):
        """Тестирование использование кеширования"""
        response = self.authorized_client.get(reverse('posts:index'))
        cache_check = response.content
        post = Post.objects.get(pk=1)
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_check)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_check)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )
        cls.post_id = cls.post.pk
        cls.post_without_group = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            image=cls.uploaded,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostImageTests.user)
        cache.clear()

    def test_image_context(self):
        """URL-адрес использует соответствующий шаблон с картинкой."""
        list = (
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.user.username}),
        )
        for page_number in list:
            with self.subTest(page_number=page_number):
                response = self.authorized_client.get(page_number)
                self.assertTrue(response.context['page_obj'][0].image)

    def test_post_detail_show_image(self):
        """Шаблон post_detail сформирован с картинкой."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'].image, self.post.image)


class FollowPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.un_subscriber = User.objects.create_user(username='un_subscriber')
        cls.subscriber = User.objects.create_user(username='follower')
        cls.author = User.objects.create_user(username='following')
        cls.subscriber_2 = User.objects.create_user(
            username='subscriber_2')
        cls.follow = Follow.objects.create(
            user=cls.subscriber,
            author=cls.author,
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.subscriber)
        self.subscriber_2_client = Client()
        self.subscriber_2_client.force_login(self.subscriber_2)
        cache.clear()

    def test_auth_user_follow(self):
        """Проверка, что авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        self.assertTrue(Follow.objects.filter(
            user=self.subscriber,
            author=self.author,
        ).exists())

    def test_unfollow_post_delete(self):
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )
        post = Post.objects.create(author=self.author)
        response = self.authorized_client.get(reverse(
            'posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'])

    def test_follow_page_follower(self):
        """Проверка, что посты появляются по подписке."""
        response = self.authorized_client.get(reverse(
            'posts:follow_index'
        ))
        follower_posts_cnt = len(response.context['page_obj'])
        self.assertEqual(follower_posts_cnt, 1)
        post = Post.objects.get(id=self.post.pk)
        self.assertIn(post, response.context['page_obj'])

    def test_follow_page_unfollower_2(self):
        """Проверка, что посты не появляются если не подписан."""
        response = self.subscriber_2_client.get(reverse(
            'posts:follow_index'))
        posts_cnt_new = len(response.context['page_obj'].object_list)
        self.assertEqual(posts_cnt_new, 0)
