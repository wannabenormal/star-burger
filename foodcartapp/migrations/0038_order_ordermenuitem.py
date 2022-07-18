# Generated by Django 3.2 on 2022-07-07 11:23

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0037_auto_20210125_1833'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(db_index=True, max_length=200, verbose_name='Адрес')),
                ('name', models.CharField(blank=True, db_index=True, max_length=50, verbose_name='Имя')),
                ('last_name', models.CharField(blank=True, db_index=True, max_length=50, verbose_name='Фамилия')),
                ('phonenumber', phonenumber_field.modelfields.PhoneNumberField(db_index=True, max_length=128, region=None, verbose_name='Телефон')),
            ],
            options={
                'verbose_name': 'заказ',
                'verbose_name_plural': 'заказы',
            },
        ),
        migrations.CreateModel(
            name='OrderMenuItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='количество')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='foodcartapp.order', verbose_name='заказ')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_items', to='foodcartapp.product', verbose_name='продукт')),
            ],
            options={
                'verbose_name': 'товар в заказе',
                'verbose_name_plural': 'товары в заказе',
                'unique_together': {('order', 'product')},
            },
        ),
    ]