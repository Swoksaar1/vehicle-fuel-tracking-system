from django.contrib import admin
from .models import Vehicle, FuelTransaction, BudgetAllocation


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle_name",
        "plate_no",
        "vehicle_type",
        "section",
        "status",
        "created_at",
    )
    search_fields = (
        "vehicle_name",
        "plate_no",
        "vehicle_type",
        "section",
        "status",
    )
    list_filter = (
        "vehicle_type",
        "section",
        "status",
        "created_at",
    )
    ordering = ("vehicle_name",)


@admin.register(FuelTransaction)
class FuelTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle_name",
        "plate_no",
        "vehicle_type",
        "section",
        "driver_name",
        "product",
        "quantity",
        "unit_price",
        "amount",
        "fund_source",
        "date",
        "created_at",
    )
    search_fields = (
        "vehicle_name",
        "plate_no",
        "driver_name",
        "destination",
        "charge_invoice_no",
        "product",
        "fund_source",
    )
    list_filter = (
        "vehicle_type",
        "section",
        "product",
        "fund_source",
        "date",
        "created_at",
    )
    ordering = ("-date", "-id")


@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    list_display = (
        "fund_type",
        "amount",
        "reference_no",
        "date_received",
        "created_at",
    )
    search_fields = (
        "fund_type",
        "reference_no",
        "remarks",
    )
    list_filter = (
        "fund_type",
        "date_received",
        "created_at",
    )
    ordering = ("-date_received", "-id")