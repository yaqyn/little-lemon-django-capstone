import decimal
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models
import restaurant.models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(unique=True)),
                ("title", models.CharField(max_length=100)),
            ],
            options={"verbose_name_plural": "categories", "ordering": ["title", "id"]},
        ),
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(max_length=100)),
                ("reservation_date", models.DateField(validators=[restaurant.models.validate_reservation_date])),
                ("reservation_slot", models.PositiveSmallIntegerField(choices=restaurant.models.SLOT_CHOICES)),
            ],
            options={
                "ordering": ["reservation_date", "reservation_slot", "id"],
                "constraints": [
                    models.UniqueConstraint(fields=("reservation_date", "reservation_slot"), name="unique_reservation_date_slot"),
                    models.CheckConstraint(condition=models.Q(reservation_slot__gte=10, reservation_slot__lte=20), name="valid_reservation_slot"),
                ],
            },
        ),
        migrations.CreateModel(
            name="MenuItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=150)),
                ("price", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.01"))])),
                ("featured", models.BooleanField(default=False)),
                ("description", models.TextField(blank=True)),
                ("image", models.CharField(blank=True, help_text="Local static image path, e.g. images/greek-salad.svg", max_length=250)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="menu_items", to="restaurant.category")),
            ],
            options={
                "ordering": ["title", "id"],
                "constraints": [models.CheckConstraint(condition=models.Q(price__gt=0), name="positive_menu_price")],
            },
        ),
    ]
