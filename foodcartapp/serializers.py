from rest_framework import serializers
from rest_framework.validators import ValidationError
import phonenumbers

from .models import Order, OrderMenuItem


class OrderMenuItemSerializer(serializers.ModelSerializer):
    product = serializers.IntegerField(source='product.id')

    class Meta:
        model = OrderMenuItem
        fields = ['product', 'quantity']


class RegisterOrderSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='name')
    lastname = serializers.CharField(source='last_name')
    products = OrderMenuItemSerializer(many=True, allow_empty=False)

    def validate_phonenumber(self, value):
        try:
            phone = phonenumbers.parse(value, 'RU')

            if not phonenumbers.is_valid_number_for_region(phone, 'RU'):
                raise ValidationError('Неверный формат телефона')
        except phonenumbers.NumberParseException:
            raise ValidationError('Неверный формат телефона')

        return value

    class Meta:
        model = Order
        fields = [
            'firstname',
            'lastname',
            'address',
            'phonenumber',
            'products'
        ]
