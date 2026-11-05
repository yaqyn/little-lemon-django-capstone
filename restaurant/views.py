import json
from datetime import date

from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods
from rest_framework import filters, serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from .models import Booking, Category, MenuItem, SLOT_CHOICES
from .permissions import PublicCreateStaffManage, StaffWriteOrReadOnly
from .serializers import BookingSerializer, CategorySerializer, MenuItemSerializer


def parse_date(raw):
    try:
        parsed = date.fromisoformat(raw)
        if parsed.isoformat() != raw:
            raise ValueError
        return parsed
    except (ValueError, TypeError):
        raise ValidationError({"date": "Supply a date in YYYY-MM-DD format."})


class RestaurantPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [StaffWriteOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        from django.db.models.deletion import ProtectedError
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError({"detail": "Move or delete this category's menu items first."})


class MenuItemViewSet(viewsets.ModelViewSet):
    pagination_class = RestaurantPagination
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    permission_classes = [StaffWriteOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["price", "title", "id"]
    ordering = ["title", "id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category_id=category) if category.isdigit() else queryset.filter(category__slug=category)
        featured = self.request.query_params.get("featured")
        if featured is not None:
            if featured.lower() not in ("true", "false", "1", "0"):
                raise ValidationError({"featured": "Use true or false."})
            queryset = queryset.filter(featured=featured.lower() in ("true", "1"))
        return queryset


class BookingViewSet(viewsets.ModelViewSet):
    pagination_class = RestaurantPagination
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [PublicCreateStaffManage]

    def get_queryset(self):
        queryset = super().get_queryset()
        raw_date = self.request.query_params.get("date")
        if raw_date is not None:
            queryset = queryset.filter(reservation_date=parse_date(raw_date))
        return queryset


@require_GET
def home(request):
    return render(request, "restaurant/home.html", {"featured_items": MenuItem.objects.select_related("category").filter(featured=True)[:3]})


@require_GET
def about(request):
    return render(request, "restaurant/about.html")


@require_GET
def menu(request):
    return render(request, "restaurant/menu.html", {"menu_items": MenuItem.objects.select_related("category").all(), "categories": Category.objects.all()})


@require_GET
def menu_detail(request, pk):
    return render(request, "restaurant/menu_detail.html", {"item": get_object_or_404(MenuItem.objects.select_related("category"), pk=pk)})


def booking_context():
    now = timezone.localtime()
    return {"today": now.date().isoformat(), "slots": SLOT_CHOICES, "current_hour": now.hour, "timezone_name": settings.TIME_ZONE}


@ensure_csrf_cookie
@csrf_protect
@require_http_methods(["GET", "POST"])
def book(request):
    if request.method == "GET":
        return render(request, "restaurant/book.html", booking_context())
    if request.content_type != "application/json":
        return JsonResponse({"detail": "Send application/json."}, status=415)
    try:
        data = json.loads(request.body)
    except RequestDataTooBig:
        return JsonResponse({"detail": "Reservation request is too large."}, status=413)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "Send a valid JSON object."}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"detail": "Send a JSON object with reservation fields."}, status=400)
    serializer = BookingSerializer(data=data)
    if serializer.is_valid():
        try:
            serializer.save()
        except serializers.ValidationError as error:
            return JsonResponse(error.detail, status=400)
        return JsonResponse(serializer.data, status=201)
    return JsonResponse(serializer.errors, status=400)


@require_GET
def reservations(request):
    return render(request, "restaurant/reservations.html", booking_context())


@require_GET
def bookings_json(request):
    try:
        selected_date = parse_date(request.GET.get("date"))
    except ValidationError as error:
        return JsonResponse(error.detail, status=400)
    records = list(Booking.objects.filter(reservation_date=selected_date).values("id", "first_name", "reservation_date", "reservation_slot"))
    if not request.user.is_staff:
        for record in records:
            record["first_name"] = "Reserved"
    response = JsonResponse(records, safe=False)
    response["Cache-Control"] = "no-store"
    return response
