from decimal import Decimal
from django.db.models import Sum
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    Vehicle,
    FuelTransaction,
    BudgetAllocation,
    FUND_SOURCE_CHOICES,
    SystemSettings,
    AdminAccount,
)

from .serializers import (
    VehicleSerializer,
    FuelTransactionSerializer,
    BudgetAllocationSerializer,
    SystemSettingsSerializer,
)


def get_or_create_system_settings():
    settings_obj, _ = SystemSettings.objects.get_or_create(
        pk=1,
        defaults={
            "system_name": "Vehicle Fuel Tracking System",
            "office_name": "CDRRMO",
            "admin_name": "Administrator",
            "admin_email": "",
        },
    )

    return settings_obj


def get_or_create_admin_account():
    account = AdminAccount.objects.order_by("id").first()

    if account:
        return account

    account = AdminAccount(username="fuel")
    account.set_password("fuel123")
    account.save()

    return account


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all().order_by("vehicle_name")
    serializer_class = VehicleSerializer


class FuelTransactionViewSet(viewsets.ModelViewSet):
    queryset = (
        FuelTransaction.objects.select_related("vehicle")
        .all()
        .order_by("-date", "-id")
    )
    serializer_class = FuelTransactionSerializer


class BudgetAllocationViewSet(viewsets.ModelViewSet):
    queryset = BudgetAllocation.objects.all().order_by("-date_received", "-id")
    serializer_class = BudgetAllocationSerializer


@api_view(["POST"])
def login_view(request):
    account = get_or_create_admin_account()

    username = str(request.data.get("username", "")).strip()
    password = str(request.data.get("password", ""))

    if not username or not password:
        return Response(
            {"detail": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if username != account.username or not account.check_password(password):
        return Response(
            {"detail": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return Response(
        {
            "message": "Login successful.",
            "username": account.username,
        }
    )


@api_view(["GET", "PUT"])
def system_settings_view(request):
    settings_obj = get_or_create_system_settings()
    account = get_or_create_admin_account()

    if request.method == "GET":
        data = SystemSettingsSerializer(settings_obj).data
        data["login_username"] = account.username

        return Response(data)

    login_username = str(request.data.get("login_username", account.username)).strip()

    if not login_username:
        return Response(
            {"detail": "Login username is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if AdminAccount.objects.exclude(pk=account.pk).filter(username=login_username).exists():
        return Response(
            {"detail": "That login username is already in use."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = SystemSettingsSerializer(
        settings_obj,
        data={
            "system_name": request.data.get("system_name", settings_obj.system_name),
            "office_name": request.data.get("office_name", settings_obj.office_name),
            "admin_name": request.data.get("admin_name", settings_obj.admin_name),
            "admin_email": request.data.get("admin_email", settings_obj.admin_email),
        },
        partial=True,
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()

    if account.username != login_username:
        account.username = login_username
        account.save()

    response_data = serializer.data
    response_data["login_username"] = account.username
    response_data["message"] = "Settings saved successfully."

    return Response(response_data)


@api_view(["POST"])
def change_password_view(request):
    account = get_or_create_admin_account()

    current_password = str(request.data.get("current_password", "")).strip()
    new_password = str(request.data.get("new_password", "")).strip()
    confirm_password = str(request.data.get("confirm_password", "")).strip()

    if not current_password or not new_password or not confirm_password:
        return Response(
            {"detail": "Please fill in all password fields."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not account.check_password(current_password):
        return Response(
            {"detail": "Current password is incorrect."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(new_password) < 4:
        return Response(
            {"detail": "New password must be at least 4 characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if new_password != confirm_password:
        return Response(
            {"detail": "New password and confirm password do not match."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if account.check_password(new_password):
        return Response(
            {"detail": "New password must be different from current password."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    account.set_password(new_password)
    account.save()

    return Response({"message": "Password changed successfully."})


@api_view(["GET"])
def dashboard_summary(request):
    year = request.GET.get("year")

    budget_queryset = BudgetAllocation.objects.all()
    fuel_queryset = FuelTransaction.objects.all()

    selected_year = None

    if year:
        try:
            selected_year = int(year)
        except ValueError:
            return Response(
                {"detail": "Invalid year."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        budget_queryset = budget_queryset.filter(date_received__year=selected_year)
        fuel_queryset = fuel_queryset.filter(fund_year=selected_year)

    total_transactions = fuel_queryset.count()

    total_amount = (
        fuel_queryset.aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    total_quantity = (
        fuel_queryset.aggregate(total=Sum("quantity"))["total"]
        or Decimal("0.00")
    )

    total_vehicles = Vehicle.objects.count()

    serviceable_units = Vehicle.objects.filter(status="Serviceable").count()
    non_serviceable_units = Vehicle.objects.filter(status="Non Serviceable").count()

    total_budget_allocated = (
        budget_queryset.aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    total_budget_used = total_amount
    total_budget_remaining = total_budget_allocated - total_budget_used

    fund_breakdown = {}

    for fund_value, _ in FUND_SOURCE_CHOICES:
        allocated = (
            budget_queryset.filter(fund_type=fund_value).aggregate(total=Sum("amount"))[
                "total"
            ]
            or Decimal("0.00")
        )

        used = (
            fuel_queryset.filter(fund_source=fund_value).aggregate(total=Sum("amount"))[
                "total"
            ]
            or Decimal("0.00")
        )

        remaining = allocated - used

        fund_breakdown[fund_value] = {
            "allocated": allocated,
            "used": used,
            "remaining": remaining,
        }

    return Response(
        {
            "year": selected_year,
            "total_transactions": total_transactions,
            "total_amount": total_amount,
            "total_quantity": total_quantity,
            "total_vehicles": total_vehicles,
            "serviceable_units": serviceable_units,
            "non_serviceable_units": non_serviceable_units,
            "total_budget_allocated": total_budget_allocated,
            "total_budget_used": total_budget_used,
            "total_budget_remaining": total_budget_remaining,
            "fund_breakdown": fund_breakdown,
        }
    )