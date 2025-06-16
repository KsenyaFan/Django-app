from string import ascii_letters
from random import choices

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.urls import reverse

from .models import Product, Order
from .utils import add_two_numbers


class AddTwoNumbersTestCase(TestCase):
    def test_add_two_numbers(self):
        result = add_two_numbers(2, 3)
        self.assertEqual(result, 5)


class ProductCreateViewTestCase(TestCase):
    def setUp(self):
        self.product_name = "".join(choices(ascii_letters, k=10))
        Product.objects.filter(name=self.product_name).delete()

    def test_create_product(self):
        response = self.client.post(
            reverse("shopapp:product_create"),
            {
                "name": self.product_name,
                "price": "123.45",
                "description": "A good table",
                "discount": "10",
            }
        )
        self.assertRedirects(response, reverse("shopapp:products_list"))
        self.assertTrue(
            Product.objects.filter(name=self.product_name).exists()
        )


class ProductDetailsViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.user = User.objects.create_user(username="Bob_test", password="qwerty")
        cls.product = Product.objects.create(name="Best Product", created_by=cls.user)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.product.delete()
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_get_product(self):
        response = self.client.get(
            reverse("shopapp:product_details", kwargs={"pk": self.product.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_get_product_and_check_content(self):
        response = self.client.get(
            reverse("shopapp:product_details", kwargs={"pk": self.product.pk})
        )
        self.assertContains(response, self.product.name)


class ProductsListViewTestCase(TestCase):
    fixtures = [
        "products-fixture.json"
    ]

    @classmethod
    def setUpClass(cls) -> None:
        cls.user = User.objects.create_user(username="Bob_test", password="qwerty")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_products(self):
        response = self.client.get(reverse("shopapp:products_list"))
        products = response.context["products"]
        # for product in Product.objects.filter(archived=False):
        #     self.assertContains(response, product.name)
        self.assertQuerysetEqual(
            qs=Product.objects.filter(archived=False).all(),
            values=(p.pk for p in response.context["products"]),
            transform=lambda p: p.pk
        )
        self.assertTemplateUsed(response, 'shopapp/products-list.html')


class OrdersListViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        # cls.credentials = dict(username="Bob_test", password="qwerty")
        # cls.user = User.objects.create_user(**cls.credentials)
        cls.user = User.objects.create_user(username="Bob_test", password="qwerty")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_orders_view(self):
        response = self.client.get(reverse("shopapp:orders_list"))
        self.assertContains(response, "Orders")

    def test_orders_view_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse("shopapp:orders_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(settings.LOGIN_URL), response.url)


class OrderDetailViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.user = User.objects.create_user(username="Bob_test", password="qwerty")
        cls.user.user_permissions.add(
            Permission.objects.get(codename="view_order")
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)
        self.order = Order.objects.create(
            delivery_address="Mitishy 44",
            promocode="SALE",
            user=self.user
        )

    def tearDown(self):
        self.order.delete()

    def test_order_details(self):
        response = self.client.get(
            reverse(
                "shopapp:order_details", kwargs={"pk": self.order.pk}
            ))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, self.order.delivery_address)
        self.assertContains(response, self.order.promocode)

        context_order = response.context["order"]
        self.assertEqual(context_order.pk, self.order.pk)


class ProductsExportViewTestCase(TestCase):
    fixtures = [
        'products-fixture.json'
    ]

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(id=1, username='admin', password='pass')

    def test_get_products_export(self):
        response = self.client.get(
            reverse('shopapp:products-export')
        )
        self.assertEqual(response.status_code, 200)
        products = Product.objects.order_by("pk").all()
        expected_data = [
            {
                "pk": product.pk,
                "name": product.name,
                "price": str(product.price),
                "archived": product.archived,
            }
            for product in products
        ]
        products_data = response.json()
        self.assertEqual(
            products_data["products"],
            expected_data
        )


class OrdersExportViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="admin", password="pass", is_staff=True)
        cls.product1 = Product.objects.create(name="phone 1", price=1000, created_by=cls.user)
        cls.product2 = Product.objects.create(name="phone 2", price=2000, created_by=cls.user)
        cls.order = Order.objects.create(
            delivery_address="Some Address",
            promocode="1234",
            user=cls.user,
        )
        cls.order.products.set([cls.product1, cls.product2])

    @classmethod
    def tearDownClass(cls) -> None:
        Order.objects.filter(user=cls.user).delete()
        cls.user.delete()

    def setUp(self):
        self.client.login(username="admin", password="pass")

    def test_orders_export_view(self):
        response = self.client.get(reverse("shopapp:orders-export"))
        self.assertEqual(response.status_code, 200)
        orders = Order.objects.order_by("pk").all()
        expected_data = {
            "orders": [
                {
                    "id": self.order.pk,
                    "delivery_address": self.order.delivery_address,
                    "promocode": self.order.promocode,
                    "user_id": self.user.id,
                    "product_id": [self.product1.id, self.product2.id],
                }
            ]
        }
        orders_data = response.json()
        self.assertEqual(orders_data, expected_data)
