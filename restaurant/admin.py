from django.contrib import admin

from .models import Booking, Category, MenuItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title",)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price", "featured")
    list_filter = ("category", "featured")
    search_fields = ("title", "description")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("first_name", "reservation_date", "reservation_slot")
    list_filter = ("reservation_date", "reservation_slot")
    search_fields = ("first_name",)
    date_hierarchy = "reservation_date"
