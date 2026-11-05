from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("menu-items", views.MenuItemViewSet, basename="menu-item")
router.register("categories", views.CategoryViewSet, basename="category")
router.register("bookings", views.BookingViewSet, basename="booking")

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("menu/", views.menu, name="menu"),
    path("menu/<int:pk>/", views.menu_detail, name="menu-detail"),
    path("book/", views.book, name="book"),
    path("reservations/", views.reservations, name="reservations"),
    path("bookings", views.bookings_json, name="bookings-json"),
    path("bookings/", views.bookings_json, name="bookings-json-slash"),
    path("api/", include(router.urls)),
]
