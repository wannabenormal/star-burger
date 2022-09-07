from django.http import JsonResponse
from django.templatetags.static import static
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Order, OrderMenuItem
from .serializers import OrderSerializer


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()
    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@transaction.atomic
@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    order = Order.objects.create(
        address=validated_data['address'],
        name=validated_data['name'],
        last_name=validated_data['last_name'],
        phonenumber=validated_data['phonenumber']
    )

    order_items = [
        OrderMenuItem(order=order, price=fields['product'].price, **fields)
        for fields in validated_data['products']
    ]

    OrderMenuItem.objects.bulk_create(order_items)

    if serializer.is_valid:
        return Response(OrderSerializer(order).data)
    return JsonResponse(serializer.errors, status=400)
