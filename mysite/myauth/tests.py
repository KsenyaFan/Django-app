import json
from django.test import TestCase
from django.urls import reverse

class GetCookieViewTestCase(TestCase):
    def test_get_cookie_view(self):
        responce = self.client.get(reverse("myauth:cookie-get"))
        self.assertContains(responce, "Cookie value")

class FooBarViewTestCase(TestCase):
    def test_foo_bar_view(self):
        responce = self.client.get(reverse("myauth:foo-bar"))
        self.assertEquals(responce.status_code, 200)
        self.assertEquals(responce.headers['content-type'], 'application/json')
        expected_data = {"foo": "bar", "spam": "eggs"}
        # reseived_data = json.loads(responce.content)
        # self.assertEquals(reseived_data, expected_data)
        self.assertJSONEqual(responce.content, expected_data)