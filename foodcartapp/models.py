from collections import defaultdict
import copy

from django.db import models
from django.db.models import Sum, F, Prefetch
from django.core.validators import MinValueValidator, RegexValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone

from locations.geo_tools import get_or_create_locations, calc_distance


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def get_orders_summary(self):
        return self.annotate(
            summary=Sum(
                F('order_items__quantity') * F('order_items__price')
            )
        )

    def with_restaurants(self):
        orders = self.prefetch_related(
            Prefetch(
                'order_items',
                queryset=OrderMenuItem.objects.select_related('product')
            )
        )

        menu_items = RestaurantMenuItem.objects.select_related(
            'restaurant',
            'product'
        ).filter(
            availability=True,
        )

        order_addresses = [order.address for order in orders]
        restaurant_addresses = [
            menu_item.restaurant.address
            for menu_item in menu_items
        ]

        locations = get_or_create_locations(
            [*order_addresses, *restaurant_addresses]
        )

        restaurants_by_items = defaultdict(list)

        for menu_item in menu_items:
            restaurants_by_items[menu_item.product.id].append(
                menu_item.restaurant
            )

        for order in orders:
            order_location = locations.get(order.address)
            order.location = order_location

            order_restaurants_by_items = [
                copy.deepcopy(restaurants_by_items[order_item.product.id])
                for order_item in order.order_items.all()
            ]
            order.restaurants = list(
                set.intersection(*[
                    set(list) for list in order_restaurants_by_items
                ])
            )

            for restaurant in order.restaurants:
                restaurant_location = locations.get(restaurant.address)
                restaurant.distance = calc_distance(
                    order_location,
                    restaurant_location
                )

            order.restaurants = sorted(
                order.restaurants,
                key=lambda restaurant: restaurant.distance
            )

        return orders


class Order(models.Model):
    CREATED = 'created'
    ASSEMBLING = 'assembling'
    DELIVERING = 'delivering'
    DONE = 'done'
    STATUS_CHOICES = [
        (CREATED, 'Необработанный'),
        (ASSEMBLING, 'Сборка'),
        (DELIVERING, 'Доставка'),
        (DONE, 'Доставлен')
    ]

    ONLINE = 'online'
    CASH = 'cash'
    PAYMENT_METHOD_CHOICES = [
        (ONLINE, 'Онлайн-оплата'),
        (CASH, 'Оплата при получении')
    ]

    created_at = models.DateTimeField(
        db_index=True,
        default=timezone.now,
        blank=True,
        null=True,
        verbose_name='Зарегистрирован в'
    )
    called_at = models.DateTimeField(
        db_index=True,
        blank=True,
        null=True,
        verbose_name='Уточнен в'
    )
    delivered_at = models.DateTimeField(
        db_index=True,
        blank=True,
        null=True,
        verbose_name='Доставлен в'
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=CREATED,
        db_index=True,
        verbose_name='Статус'
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        db_index=True,
        blank=True,
        verbose_name='Способ оплаты'
    )
    address = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name='Адрес'
    )
    name = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=50, blank=True,
        db_index=True, verbose_name='Фамилия'
    )

    phonenumber_regex = RegexValidator(regex=r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$')
    phonenumber = PhoneNumberField(
        db_index=True,
        validators=[phonenumber_regex],
        verbose_name='Телефон',
        region='RU'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий к заказу'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Ресторан'
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.name} {self.last_name} {self.address}'


class OrderMenuItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='заказ'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items',
        verbose_name='продукт'
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='количество'
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True
    )

    class Meta:
        verbose_name = 'товар в заказе'
        verbose_name_plural = 'товары в заказе'
        unique_together = [
            ['order', 'product']
        ]

    def __str__(self):
        return f'{self.product.name} {self.order}'
