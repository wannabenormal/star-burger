from django.db import models
from django.utils import timezone


class Location(models.Model):
    address = models.CharField(max_length=60, unique=True, verbose_name='Адрес')
    lat = models.FloatField(verbose_name='Ширина', null=True, blank=True)
    lon = models.FloatField(verbose_name='Долгота', null=True, blank=True)
    date = models.DateField(
        default=timezone.now,
        verbose_name='Дата запроса к Геокодеру'
    )
