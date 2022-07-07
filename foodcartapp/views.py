from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import phonenumbers


from .models import Product, Order, OrderMenuItem


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


@api_view(['POST'])
def register_order(request):
    USER_FIELDS = ['address', 'firstname', 'lastname', 'phonenumber']

    order_response = request.data

    missed_user_fields = []
    null_user_fields = []
    bad_type_fields = []

    for field_name in USER_FIELDS:
        try:
            field_value = order_response[field_name]

            if field_value is None:
                null_user_fields.append(field_name)

            if not isinstance(field_value, str):
                bad_type_fields.append(field_name)
        except KeyError:
            missed_user_fields.append(field_name)

    if len(missed_user_fields):
        return Response(
            {
                'status': 'error',
                'message': '{}: Обязательное поле'.format(
                    ', '.join(missed_user_fields)
                )
            },
            status=status.HTTP_406_NOT_ACCEPTABLE
        )

    if len(null_user_fields):
        return Response(
            {
                'status': 'error',
                'message': '{}: Поле не может быть пустым'.format(
                    ', '.join(null_user_fields)
                )
            },
            status=status.HTTP_406_NOT_ACCEPTABLE
        )

    if len(bad_type_fields):
        return Response(
            {
                'status': 'error',
                'message': '{}: Поле должно быть str'.format(
                    ', '.join(bad_type_fields)
                )
            },
            status=status.HTTP_406_NOT_ACCEPTABLE
        )

    try:
        phone = phonenumbers.parse(order_response['phonenumber'], 'RU')

        if not phonenumbers.is_valid_number_for_region(phone, 'RU'):
            raise Exception()
    except Exception:
        return Response(
            {
                'status': 'error',
                'message': 'phonenumber: Неверный формат телефона'
            },
            status=status.HTTP_406_NOT_ACCEPTABLE
        )

    try:
        products = order_response['products']
    except KeyError:
        return Response(
            {
                'status': 'error',
                'message': 'products: обязательное поле'
            },
            status=status.HTTP_406_NOT_ACCEPTABLE
        )

    if products is None:
        return Response(
            {
                'status': 'error',
                'message': 'products: Это поле не может быть пустым'
            },
            status=status.HTTP_406_NOT_ACCEPTABLE
        )

    if not isinstance(products, list):
        return Response(
            {
                'status': 'error',
                'message': 'products: Ожидается list.'
            },
            status=status.HTTP_406_NOT_ACCEPTABLE
        )

    if not len(products):
        return Response(
            {
                'status': 'error',
                'message': 'products: Этот список не может быть пустым'
            },
            status=status.HTTP_406_NOT_ACCEPTABLE
        )

    order = Order.objects.create(
        address=order_response['address'],
        name=order_response['firstname'],
        last_name=order_response['lastname'],
        phonenumber=order_response['phonenumber']
    )

    for product in products:
        try:
            product_id = product['product']
            Product.objects.get(id=product_id)
            OrderMenuItem.objects.create(
                product_id=product_id,
                order=order,
                quantity=product['quantity']
            )
        except Product.DoesNotExist:
            return Response(
                {
                    'status': 'error',
                    'message': f'Недопустимый первичный ключ "{product_id}"'
                }
            )

    return Response(order_response)
