import requests
from geopy import distance

from django.conf import settings
from .models import Location


def fetch_coordinates(address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": settings.YANDEX_API_KEY,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')

    return lat, lon


def calc_distance(point_one, point_two):
    return round(distance.distance(point_one, point_two).km, 2)


def get_or_create_locations(addresses):
    locations_with_coords = {
        location.address: (location.lat, location.lon)
        for location in Location.objects.filter(address__in=addresses)
    }

    new_locations = []

    for address in addresses:
        if address in locations_with_coords.keys():
            continue

        coordinates = fetch_coordinates(address)

        if coordinates:
            lat, lon = coordinates
            new_location = Location(
                address=address,
                lat=lat,
                lon=lon
            )

            locations_with_coords[address] = (lat, lon)
        else:
            new_location = Location(
                address=address
            )
            locations_with_coords[address] = None

        new_locations.append(new_location)

    if len(new_locations) > 0:
        Location.objects.bulk_create(new_locations)

    return locations_with_coords
