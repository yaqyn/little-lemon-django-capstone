from django.core.management.base import BaseCommand
from django.db import transaction

from restaurant.models import Category, MenuItem


class Command(BaseCommand):
    help = "Create or refresh the demonstration menu; never creates users or reservations."

    @transaction.atomic
    def handle(self, *args, **options):
        starters, _ = Category.objects.get_or_create(slug="starters", defaults={"title": "Starters"})
        mains, _ = Category.objects.get_or_create(slug="mains", defaults={"title": "Mains"})
        desserts, _ = Category.objects.get_or_create(slug="desserts", defaults={"title": "Desserts"})
        items = [
            ("Greek salad", "12.50", starters, "Crisp cucumber, ripe tomatoes, Kalamata olives and feta, dressed with olive oil and oregano.", "greek-salad.svg", True),
            ("Bruschetta", "8.00", starters, "Toasted bread with marinated tomatoes, fresh basil and a drizzle of olive oil.", "bruschetta.svg", True),
            ("Lemon chicken", "19.50", mains, "Grilled chicken with lemon, rosemary, seasonal vegetables and roasted potatoes.", "lemon-chicken.svg", False),
            ("Garden pasta", "16.00", mains, "Pasta tossed with seasonal vegetables, garlic and a bright tomato sauce.", "pasta.svg", False),
            ("Lemon dessert", "7.50", desserts, "A slice of lemon cake with a delicate citrus glaze.", "lemon-dessert.svg", True),
        ]
        for title, price, category, description, image, featured in items:
            MenuItem.objects.update_or_create(title=title, defaults={"price": price, "category": category, "description": description, "image": f"images/{image}", "featured": featured})
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(items)} menu items."))
