"""Behavioral coverage for the restaurant website, API and access boundaries."""
from datetime import timedelta
from decimal import Decimal
import json
import re

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Booking, Category, MenuItem


class RestaurantTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(slug="mains", title="Mains")
        cls.item = MenuItem.objects.create(title="Lemon pasta", price=Decimal("15.50"),
                                          category=cls.category, description="Fresh lemon pasta", featured=True)
        cls.staff = get_user_model().objects.create_user("chef", password="Kitchen-Secure-783!", is_staff=True)
        cls.user = get_user_model().objects.create_user("diner", password="Diner-Secure-783!")
        cls.day = timezone.localdate() + timedelta(days=7)

    def setUp(self):
        self.api = APIClient()

    def payload(self, **changes):
        data = {"first_name": "Jordan", "reservation_date": str(self.day), "reservation_slot": 12}
        data.update(changes)
        return data

    def menu_payload(self, **changes):
        data = {"title": "Greek salad", "price": "12.00", "category": self.category.pk,
                "description": "Tomatoes and olives", "featured": False}
        data.update(changes)
        return data

    def staff_login(self):
        self.api.force_authenticate(self.staff)

    def make_booking(self, **changes):
        return Booking.objects.create(**self.payload(**changes))

    def test_homepage(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_all_website_pages(self):
        for path in ["/about/", "/menu/", f"/menu/{self.item.pk}/", "/book/", "/reservations/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_menu_renders_database_content(self):
        self.assertContains(self.client.get("/menu/"), "Lemon pasta")

    def test_menu_api_lists_and_retrieves(self):
        response = self.api.get("/api/menu-items/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["title"], "Lemon pasta")
        self.assertEqual(self.api.get(f"/api/menu-items/{self.item.pk}/").status_code, 200)

    def test_staff_creates_menu_item(self):
        self.staff_login()
        response = self.api.post("/api/menu-items/", self.menu_payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(MenuItem.objects.filter(title="Greek salad").exists())

    def test_anonymous_cannot_modify_menu(self):
        for method in ["post", "put", "patch", "delete"]:
            path = "/api/menu-items/" if method == "post" else f"/api/menu-items/{self.item.pk}/"
            with self.subTest(method=method):
                self.assertIn(getattr(self.api, method)(path, self.menu_payload(), format="json").status_code, [401, 403])

    def test_regular_user_cannot_modify_menu(self):
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.post("/api/menu-items/", self.menu_payload(), format="json").status_code, 403)

    def test_staff_put_patch_delete_menu(self):
        self.staff_login()
        url = f"/api/menu-items/{self.item.pk}/"
        self.assertEqual(self.api.put(url, self.menu_payload(), format="json").status_code, 200)
        self.assertEqual(self.api.patch(url, {"price": "14.25"}, format="json").status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.price, Decimal("14.25"))
        self.assertEqual(self.api.delete(url).status_code, 204)

    def test_invalid_price_rejected(self):
        self.staff_login()
        for price in ["-1.00", "bad", "1.001"]:
            with self.subTest(price=price):
                self.assertEqual(self.api.post("/api/menu-items/", self.menu_payload(price=price), format="json").status_code, 400)

    def test_invalid_category_rejected(self):
        self.staff_login()
        self.assertEqual(self.api.post("/api/menu-items/", self.menu_payload(category=999999), format="json").status_code, 400)

    def test_missing_menu_fields_rejected(self):
        self.staff_login()
        self.assertEqual(self.api.post("/api/menu-items/", {}, format="json").status_code, 400)

    def test_menu_search_and_ordering(self):
        MenuItem.objects.create(title="Soup", price="5.00", category=self.category)
        response = self.api.get("/api/menu-items/?search=lemon")
        self.assertEqual(response.data["count"], 1)
        response = self.api.get("/api/menu-items/?ordering=price")
        self.assertEqual(response.data["results"][0]["title"], "Soup")

    def test_category_browsing(self):
        response = self.api.get("/api/categories/")
        self.assertEqual(response.status_code, 200)

    def test_public_booking_creation(self):
        response = self.api.post("/api/bookings/", self.payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Booking.objects.count(), 1)

    def test_duplicate_booking_rejected(self):
        self.make_booking()
        response = self.api.post("/api/bookings/", self.payload(first_name="Another diner"), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Booking.objects.count(), 1)

    def test_database_constraint_prevents_duplicate(self):
        self.make_booking()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_booking(first_name="Second")

    def test_different_day_same_slot_allowed(self):
        self.make_booking()
        response = self.api.post("/api/bookings/", self.payload(reservation_date=str(self.day + timedelta(days=1))), format="json")
        self.assertEqual(response.status_code, 201)

    def test_invalid_booking_inputs(self):
        invalid = [{}, self.payload(first_name=""), self.payload(reservation_date="bad"),
                   self.payload(reservation_date=str(timezone.localdate() - timedelta(days=1))),
                   self.payload(reservation_slot=9), self.payload(reservation_slot=21),
                   self.payload(reservation_slot="noon")]
        for payload in invalid:
            with self.subTest(payload=payload):
                self.assertEqual(self.api.post("/api/bookings/", payload, format="json").status_code, 400)

    def test_booking_list_protected(self):
        self.assertIn(self.api.get("/api/bookings/").status_code, [401, 403])
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.get("/api/bookings/").status_code, 403)

    def test_staff_booking_list_filter_and_detail(self):
        booking = self.make_booking()
        self.make_booking(reservation_date=str(self.day + timedelta(days=1)))
        self.staff_login()
        response = self.api.get(f"/api/bookings/?date={self.day}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(self.api.get(f"/api/bookings/{booking.pk}/").status_code, 200)

    def test_staff_put_patch_delete_booking(self):
        booking = self.make_booking()
        self.staff_login()
        url = f"/api/bookings/{booking.pk}/"
        self.assertEqual(self.api.put(url, self.payload(first_name="Alex"), format="json").status_code, 200)
        self.assertEqual(self.api.patch(url, {"reservation_slot": 13}, format="json").status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.reservation_slot, 13)
        self.assertEqual(self.api.delete(url).status_code, 204)

    def test_regular_user_cannot_read_or_modify_booking(self):
        booking = self.make_booking()
        self.api.force_authenticate(self.user)
        for method in ["get", "put", "patch", "delete"]:
            with self.subTest(method=method):
                response = getattr(self.api, method)(f"/api/bookings/{booking.pk}/", self.payload(), format="json")
                self.assertEqual(response.status_code, 403)

    def test_public_compatibility_route_filters_and_redacts(self):
        self.make_booking()
        self.make_booking(reservation_date=str(self.day + timedelta(days=1)))
        for suffix in ["", "/"]:
            response = self.api.get(f"/bookings{suffix}?date={self.day}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), 1)
            self.assertEqual(response.json()[0]["first_name"], "Reserved")
            self.assertEqual(response.json()[0]["reservation_date"], str(self.day))
            self.assertNotIn("Jordan", response.content.decode())

    def test_compatibility_route_empty_and_bad_date(self):
        self.assertEqual(self.api.get(f"/bookings?date={self.day}").json(), [])
        for query in ["", "?date=bad"]:
            self.assertEqual(self.api.get("/bookings" + query).status_code, 400)

    def test_staff_compatibility_route_includes_name(self):
        self.make_booking()
        self.client.force_login(self.staff)
        response = self.client.get(f"/bookings?date={self.day}")
        self.assertEqual(response.json()[0]["first_name"], "Jordan")

    def test_invalid_ids_are_404(self):
        self.assertEqual(self.api.get("/api/menu-items/999999/").status_code, 404)
        self.assertEqual(self.client.get("/menu/999999/").status_code, 404)
        self.staff_login()
        self.assertEqual(self.api.get("/api/bookings/999999/").status_code, 404)

    def test_registration_hashes_password(self):
        response = self.api.post("/auth/users/", {"username": "newdiner", "password": "Dinner-Secure-984!"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        user = get_user_model().objects.get(username="newdiner")
        self.assertTrue(user.check_password("Dinner-Secure-984!"))
        self.assertNotEqual(user.password, "Dinner-Secure-984!")
        self.assertFalse(user.is_staff)

    def test_registration_rejects_weak_password(self):
        response = self.api.post("/auth/users/", {"username": "newdiner", "password": "123"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_token_login_me_and_logout(self):
        response = self.api.post("/auth/token/login/", {"username": "diner", "password": "Diner-Secure-783!"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        token = response.data["auth_token"]
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(self.api.get("/auth/users/me/").status_code, 200)
        self.assertEqual(self.api.post("/auth/token/logout/").status_code, 204)
        self.assertEqual(self.api.get("/auth/users/me/").status_code, 401)

    def test_invalid_credentials_and_missing_auth(self):
        self.assertEqual(self.api.post("/auth/token/login/", {"username": "diner", "password": "wrong"}, format="json").status_code, 400)
        self.assertEqual(self.api.get("/auth/users/me/").status_code, 401)
        self.api.credentials(HTTP_AUTHORIZATION="Token invalid")
        self.assertEqual(self.api.get("/auth/users/me/").status_code, 401)

    def test_website_booking_requires_csrf_and_saves_with_token(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/book/", json.dumps(self.payload()), content_type="application/json").status_code, 403)
        page = client.get("/book/")
        self.assertEqual(page.status_code, 200)
        token = client.cookies["csrftoken"].value
        response = client.post("/book/", json.dumps(self.payload()), content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Booking.objects.count(), 1)

    def test_booking_update_duplicate_rejected(self):
        self.make_booking()
        second = self.make_booking(reservation_slot=13)
        self.staff_login()
        response = self.api.patch(f"/api/bookings/{second.pk}/", {"reservation_slot": 12}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_zero_price_rejected(self):
        self.staff_login()
        self.assertEqual(self.api.post("/api/menu-items/", self.menu_payload(price="0.00"), format="json").status_code, 400)

    def test_menu_category_featured_and_pagination(self):
        other = Category.objects.create(slug="desserts", title="Desserts")
        MenuItem.objects.create(title="Cake", price="5.00", category=other, featured=False)
        for category in [str(self.category.pk), "mains"]:
            response = self.api.get(f"/api/menu-items/?category={category}")
            self.assertEqual(response.data["count"], 1)
            self.assertEqual(response.data["results"][0]["id"], self.item.pk)
        response = self.api.get("/api/menu-items/?featured=false")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Cake")
        response = self.api.get("/api/menu-items/?page_size=1")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(self.api.get("/api/menu-items/?featured=invalid").status_code, 400)

    def test_website_booking_rejects_malformed_json(self):
        for body in ["{", "[]", '"text"']:
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/book/", body, content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/book/", self.payload()).status_code, 415)

    def test_today_started_slot_rejected_and_future_slot_allowed(self):
        from datetime import datetime
        from unittest.mock import patch
        from zoneinfo import ZoneInfo
        now = datetime(2027, 5, 20, 12, 30, tzinfo=ZoneInfo("America/Chicago"))
        with patch("restaurant.serializers.timezone.localtime", return_value=now):
            for hour in [10, 12]:
                response = self.api.post("/api/bookings/", self.payload(reservation_date="2027-05-20", reservation_slot=hour), format="json")
                self.assertEqual(response.status_code, 400)
            response = self.api.post("/api/bookings/", self.payload(reservation_date="2027-05-20", reservation_slot=13), format="json")
            self.assertEqual(response.status_code, 201, response.data)

    def test_real_staff_token_authorizes_menu_write(self):
        login = self.api.post("/auth/token/login/", {"username": "chef", "password": "Kitchen-Secure-783!"}, format="json")
        self.assertEqual(login.status_code, 200)
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {login.data['auth_token']}")
        response = self.api.post("/api/menu-items/", self.menu_payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.api.get("/api/bookings/").status_code, 200)


    def test_reservations_page_displays_all_dates_as_json(self):
        self.make_booking()
        self.make_booking(reservation_date=str(self.day + timedelta(days=1)), reservation_slot=13)
        response = self.client.get("/reservations/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="all-bookings-json"')
        records = json.loads(response.context["bookings_json"])
        self.assertEqual(len(records), 2)
        self.assertEqual({record["reservation_date"] for record in records},
                         {str(self.day), str(self.day + timedelta(days=1))})
        self.assertTrue(all(record["first_name"] == "Reserved" for record in records))
        self.assertNotIn("Jordan", response.content.decode())
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_reservations_json_contains_all_records_without_pagination(self):
        for offset in range(15):
            self.make_booking(reservation_date=str(self.day + timedelta(days=offset)))
        response = self.client.get("/reservations/?format=json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertEqual(len(response.json()), 15)
        self.assertTrue(all(record["first_name"] == "Reserved" for record in response.json()))
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_empty_reservations_json_and_html_are_valid(self):
        response = self.client.get("/reservations/?format=json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        page = self.client.get("/reservations/")
        self.assertEqual(json.loads(page.context["bookings_json"]), [])
        self.assertContains(page, 'id="all-bookings-json"')

    def test_staff_can_read_all_reservation_names(self):
        self.make_booking()
        self.client.force_login(self.staff)
        response = self.client.get("/reservations/?format=json")
        self.assertEqual(response.json()[0]["first_name"], "Jordan")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        page = self.client.get("/reservations/")
        self.assertEqual(json.loads(page.context["bookings_json"])[0]["first_name"], "Jordan")
        self.assertEqual(page.headers["Cache-Control"], "no-store")

    def test_regular_users_receive_redacted_all_reservations(self):
        self.make_booking()
        self.client.force_login(self.user)
        response = self.client.get("/reservations/?format=json")
        self.assertEqual(response.json()[0]["first_name"], "Reserved")
        self.assertNotIn("Jordan", response.content.decode())

    def test_staff_reservation_json_display_escapes_html(self):
        malicious_name = '</pre><script>alert("reservation")</script>'
        self.make_booking(first_name=malicious_name)
        self.client.force_login(self.staff)
        page = self.client.get("/reservations/")
        self.assertEqual(json.loads(page.context["bookings_json"])[0]["first_name"], malicious_name)
        self.assertNotIn(malicious_name, page.content.decode())
        self.assertContains(page, "&lt;script&gt;")

    def test_all_reservations_json_is_not_limited_by_selected_date(self):
        self.make_booking()
        self.make_booking(reservation_date=str(self.day + timedelta(days=1)))
        response = self.client.get(f"/reservations/?format=json&date={self.day}")
        self.assertEqual(len(response.json()), 2)
        filtered = self.client.get(f"/bookings?date={self.day}")
        self.assertEqual(len(filtered.json()), 1)

    def test_booking_html_contains_native_date_today_and_active_fetch(self):
        response = self.client.get("/book/")
        source = response.content.decode()
        date_input = re.search(r'<input\b(?=[^>]*\bid="reservation_date")[^>]*>', source).group()
        today = timezone.localdate().isoformat()
        self.assertIn('type="date"', date_input)
        self.assertIn(f'value="{today}"', date_input)
        self.assertIn(f'min="{today}"', date_input)
        scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', source, re.DOTALL)
        self.assertTrue(any("littleLemonBookingFetch" in script and re.search(r'\bfetch\s*\(', script)
                            for script in scripts), "Booking HTML must contain an executable fetch call.")

    def test_website_duplicate_booking_rejected_without_creating_second_record(self):
        first = self.client.post("/book/", json.dumps(self.payload()), content_type="application/json")
        self.assertEqual(first.status_code, 201)
        duplicate = self.client.post("/book/", json.dumps(self.payload(first_name="Second diner")),
                                     content_type="application/json")
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("reservation_slot", duplicate.json())
        self.assertEqual(Booking.objects.count(), 1)
