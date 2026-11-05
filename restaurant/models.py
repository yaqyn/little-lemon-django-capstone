from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


SLOT_CHOICES = [(hour, f"{hour if hour <= 12 else hour - 12} {'AM' if hour < 12 else 'PM'}") for hour in range(10, 21)]


def validate_reservation_date(value):
    if value < timezone.localdate():
        raise ValidationError("Choose today or a future date.")


class Category(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=100)

    class Meta:
        ordering = ["title", "id"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.title


class MenuItem(models.Model):
    title = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    featured = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="menu_items")
    description = models.TextField(blank=True)
    image = models.CharField(max_length=250, blank=True, help_text="Local static image path, e.g. images/greek-salad.svg")

    class Meta:
        ordering = ["title", "id"]
        constraints = [models.CheckConstraint(condition=models.Q(price__gt=0), name="positive_menu_price")]

    def __str__(self):
        return self.title


class Booking(models.Model):
    first_name = models.CharField(max_length=100)
    reservation_date = models.DateField(validators=[validate_reservation_date])
    reservation_slot = models.PositiveSmallIntegerField(choices=SLOT_CHOICES)

    class Meta:
        ordering = ["reservation_date", "reservation_slot", "id"]
        constraints = [
            models.UniqueConstraint(fields=["reservation_date", "reservation_slot"], name="unique_reservation_date_slot"),
            models.CheckConstraint(condition=models.Q(reservation_slot__gte=10, reservation_slot__lte=20), name="valid_reservation_slot"),
        ]

    def clean(self):
        super().clean()
        now = timezone.localtime()
        if self.reservation_date == now.date() and self.reservation_slot <= now.hour:
            raise ValidationError({"reservation_slot": "Choose a future time slot."})
        if not self.first_name.strip():
            raise ValidationError({"first_name": "Enter a reservation name."})

    def __str__(self):
        return f"{self.first_name} — {self.reservation_date} {self.get_reservation_slot_display()}"
