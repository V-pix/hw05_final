from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
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
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_urls_authorized(self):
        """Проверка URL-адресов и шаблонов
        для авторизированных пользователей"""
        urls_templates = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
        }
        for url, template in urls_templates.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_unauthorized(self):
        """Проверка URL-адресов и шаблонов
        для неавторзированных пользователей"""
        urls_templates = {
            '/create/': 'users/login.html',
            f'/posts/{self.post.id}/edit/': 'users/login.html'
        }
        for url, template in urls_templates.items():
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                self.assertTemplateUsed(response, template)

    def test_create_url_redirect_guest_client(self):
        """Страница по адресу /create/ перенаправит
        неавторзированного пользователя на страницу логина."""
        url = reverse('posts:post_create')
        response = self.client.get(url)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_guest_client(self):
        """Страница по адресу /post_edit/ перенаправит
        неавторзированного пользователя на страницу логина."""
        url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        response = self.client.post(url)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_404(self):
        """Проверка, что запрос к несуществующей странице вернёт ошибку 404."""
        response = self.client.get('/about/тест/')
        self.assertEqual(response.status_code, 404)
