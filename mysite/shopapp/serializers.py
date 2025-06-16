from rest_framework import serializers

from .models import Product, Order

class ProductSerializers(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "pk",
            "name",
            "price",
            "description",
            "discount",
            "created_at",
            "archived",
            "preview",
        )


class OrderSerializers(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"