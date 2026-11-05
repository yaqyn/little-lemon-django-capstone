"""Exercise a running local server against the configured development database.

Run: pipenv run python scripts/smoke_http.py
Uses temporary records, removed in finally; never run against a production database.
"""
import json
import os
from pathlib import Path
import secrets
import sys
from datetime import timedelta
from html.parser import HTMLParser
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'littlelemon.settings')
import django
django.setup()
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from restaurant.models import Booking, Category, MenuItem

if not settings.DEBUG:
    raise SystemExit('HTTP smoke tests require a DEBUG development database.')
BASE = 'http://127.0.0.1:8000'
checks = 0

def request(path, method='GET', data=None, token=None, expected=200):
    global checks
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'
    req = Request(BASE + path, data=json.dumps(data).encode() if data is not None else None, headers=headers, method=method)
    try:
        response = urlopen(req, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        body = response.read()
        assert response.status == expected, f'{method} {path}: {response.status} expected {expected}'
        checks += 1
        return json.loads(body) if 'application/json' in response.headers.get('Content-Type', '') and body else body.decode()

class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('src', 'href') and value and value.startswith('/static/'):
                self.paths.add(value)

suffix = secrets.token_hex(8)
username = 'smoke_' + suffix
staffname = 'staff_' + suffix
password = secrets.token_urlsafe(24)
item_id = booking_id = category_id = None
try:
    request('/auth/users/', 'POST', {'username': username, 'password': password}, expected=201)
    login = request('/auth/token/login/', 'POST', {'username': username, 'password': password})
    token = login['auth_token']
    request('/auth/users/me/', token=token)
    request('/api/bookings/', token=token, expected=403)
    get_user_model().objects.create_user(staffname, password=password, is_staff=True)
    staff_token = request('/auth/token/login/', 'POST', {'username': staffname, 'password': password})['auth_token']
    category_id = request('/api/categories/', 'POST', {'slug': 'smoke-' + suffix, 'title': 'Smoke category'}, staff_token, 201)['id']
    payload = {'title': 'Smoke dish ' + suffix, 'price': '12.50', 'category': category_id}
    request('/api/menu-items/', 'POST', payload, token, 403)
    item_id = request('/api/menu-items/', 'POST', payload, staff_token, 201)['id']
    request('/api/menu-items/')
    request(f'/api/menu-items/{item_id}/')
    request(f'/api/menu-items/{item_id}/', 'PUT', payload, staff_token)
    request(f'/api/menu-items/{item_id}/', 'PATCH', {'price': '13.25'}, staff_token)
    day = timezone.localdate() + timedelta(days=500)
    while Booking.objects.filter(reservation_date=day, reservation_slot=12).exists():
        day += timedelta(days=1)
    booking = {'first_name': 'HTTP smoke test', 'reservation_date': str(day), 'reservation_slot': 12}
    booking_id = request('/api/bookings/', 'POST', booking, expected=201)['id']
    request('/api/bookings/', 'POST', booking, expected=400)
    available = request(f'/bookings?date={day}')
    assert any(row['reservation_slot'] == 12 and row['first_name'] == 'Reserved' for row in available)
    request(f'/api/bookings/?date={day}', token=staff_token)
    request(f'/api/bookings/{booking_id}/', token=staff_token)
    request(f'/api/bookings/{booking_id}/', 'PUT', booking, staff_token)
    request(f'/api/bookings/{booking_id}/', 'PATCH', {'first_name': 'Updated smoke'}, staff_token)
    assets = Assets()
    for path in ['/', '/about/', '/menu/', f'/menu/{item_id}/', '/book/', '/reservations/']:
        assets.feed(request(path))
    for path in sorted(assets.paths):
        request(path)
    request(f'/api/bookings/{booking_id}/', 'DELETE', token=staff_token, expected=204)
    request(f'/api/menu-items/{item_id}/', 'DELETE', token=staff_token, expected=204)
    request(f'/api/categories/{category_id}/', 'DELETE', token=staff_token, expected=204)
    request('/auth/token/logout/', 'POST', token=token, expected=204)
    request('/auth/users/me/', token=token, expected=401)
    print(f'{checks} live HTTP checks passed; temporary records removed.')
finally:
    if booking_id:
        Booking.objects.filter(pk=booking_id).delete()
    if item_id:
        MenuItem.objects.filter(pk=item_id).delete()
    if category_id:
        Category.objects.filter(pk=category_id).delete()
    get_user_model().objects.filter(username__in=[username, staffname]).delete()
