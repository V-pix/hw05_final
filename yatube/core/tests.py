from django.test import TestCase
from django.urls import reverse


class ViewTestClass(TestCase):
    def test_error_page(self):
        self.client.get('/nonexist-page/')

    def test_about_page_uses_correct_template(self):
        """URL-адрес использует шаблон core/404.html."""
        response = self.authorized_client.get(reverse('core:handler404'))
        self.assertTemplateUsed(response, 'core/404.html')

    def test_about_page_uses_correct_template(self):
        """статус ответа сервера - 404."""
        response = self.client.get('core/404/')
        self.assertEqual(response.status_code, 404)
