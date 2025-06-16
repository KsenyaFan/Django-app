from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction

from shopapp.models import Order, Product


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write("Start demo select fields")

        result = Product.objects.filter(
            name__contains="Aphone",
        ).update(discount=10)
        print(result)

        # info = [
        #     ('Aphone 1', 199),
        #     ('Aphone 2', 299),
        #     ('Aphone 3', 399),
        # ]
        # user = User.objects.get(id=1)
        #
        # products = [
        #     Product(name=name, price=price, created_by=user)
        #     for name, price in info
        # ]
        #
        # result = Product.objects.bulk_create(products)
        #
        # for obj in result:
        #     print(obj)

        self.stdout.write("Done")