from rest_framework import serializers
from rest_framework.serializers import ValidationError

from .models import Order, OrderMenuItem


class OrderMenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderMenuItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='name')
    lastname = serializers.CharField(source='last_name')
    products = OrderMenuItemSerializer(
        many=True,
        allow_empty=False,
        write_only=True
    )

    def validate_products(self, value):
        if isinstance(value, list) and len(value) > 0:
            return value

        raise ValidationError('Отсутствуют ключи продуктов или передан не список')

    class Meta:
        model = Order
        fields = [
            'firstname',
            'lastname',
            'address',
            'phonenumber',
            'products'
        ]
