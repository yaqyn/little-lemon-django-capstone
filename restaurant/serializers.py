from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Booking, Category, MenuItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "slug", "title"]


class MenuItemSerializer(serializers.ModelSerializer):
    category_title = serializers.CharField(source="category.title", read_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "featured", "category", "category_title", "description", "image"]

    def validate_image(self, value):
        if value and (not value.startswith("images/") or ".." in value or ":" in value or "\\" in value):
            raise serializers.ValidationError("Use a local path within images/.")
        return value


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "first_name", "reservation_date", "reservation_slot"]
        # Explicit validation also handles PATCH against the instance's unchanged values.
        validators = []

    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            unexpected = sorted(set(data.keys()) - set(self.fields))
            if unexpected:
                names = ", ".join(unexpected)
                raise serializers.ValidationError(
                    {"non_field_errors": [f"Unexpected reservation field(s): {names}."]}
                )
        return super().to_internal_value(data)

    def validate(self, attrs):
        date = attrs.get("reservation_date", getattr(self.instance, "reservation_date", None))
        slot = attrs.get("reservation_slot", getattr(self.instance, "reservation_slot", None))
        now = timezone.localtime()
        if date and slot is not None:
            if date < now.date():
                raise serializers.ValidationError({"reservation_date": "Choose today or a future date."})
            if date == now.date() and slot <= now.hour:
                raise serializers.ValidationError({"reservation_slot": "Choose a future time slot."})
            existing = Booking.objects.filter(reservation_date=date, reservation_slot=slot)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError({"reservation_slot": "This time slot is already reserved. Choose another time."})
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"reservation_slot": "This time slot is already reserved. Choose another time."})

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"reservation_slot": "This time slot is already reserved. Choose another time."})
