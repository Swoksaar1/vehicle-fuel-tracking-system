from decimal import Decimal
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


VEHICLE_TYPE_CHOICES = [
    ("Rescue Vehicle", "Rescue Vehicle"),
    ("Mobile", "Mobile"),
    ("Bus", "Bus"),
    ("Ambulance", "Ambulance"),
    ("Van", "Van"),
    ("Equipment", "Equipment"),
    ("Others", "Others"),
]

SECTION_CHOICES = [
    ("EMS", "EMS"),
    ("SAR", "SAR"),
    ("TLD", "TLD"),
    ("Others", "Others"),
]

VEHICLE_STATUS_CHOICES = [
    ("Serviceable", "Serviceable"),
    ("Non Serviceable", "Non Serviceable"),
]

PRODUCT_CHOICES = [
    ("Diesel", "Diesel"),
    ("Regular", "Regular"),
    ("Extra", "Extra"),
]

FUND_SOURCE_CHOICES = [
    ("CDRRMO Fund", "CDRRMO Fund"),
    ("Trust Fund", "Trust Fund"),
    ("LDRRM Fund", "LDRRM Fund"),
    ("SB#1", "SB#1"),
    ("Quick Respond Fund", "Quick Respond Fund"),
]


class Vehicle(models.Model):
    vehicle_name = models.CharField(max_length=150)
    plate_no = models.CharField(max_length=50, blank=True, null=True)
    vehicle_type = models.CharField(
        max_length=50,
        choices=VEHICLE_TYPE_CHOICES,
        default="Rescue Vehicle",
    )
    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES,
        default="EMS",
    )
    status = models.CharField(
        max_length=30,
        choices=VEHICLE_STATUS_CHOICES,
        default="Serviceable",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        plate = f" - {self.plate_no}" if self.plate_no else ""
        return f"{self.vehicle_name}{plate}"


class BudgetAllocation(models.Model):
    fund_type = models.CharField(
        max_length=50,
        choices=FUND_SOURCE_CHOICES,
        default="CDRRMO Fund",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference_no = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    date_received = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fund_type} - {self.amount}"


class FuelTransaction(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        related_name="fuel_transactions",
        blank=True,
        null=True,
    )

    vehicle_name = models.CharField(max_length=150)
    vehicle_type = models.CharField(
        max_length=50,
        choices=VEHICLE_TYPE_CHOICES,
        default="Rescue Vehicle",
    )
    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES,
        default="EMS",
    )
    plate_no = models.CharField(max_length=50, blank=True, null=True)

    driver_name = models.CharField(max_length=150)
    destination = models.CharField(max_length=150, blank=True, null=True)
    odometer = models.CharField(max_length=50, blank=True, null=True)
    charge_invoice_no = models.CharField(max_length=100)

    product = models.CharField(
        max_length=20,
        choices=PRODUCT_CHOICES,
        default="Diesel",
    )

    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    fund_source = models.CharField(
        max_length=50,
        choices=FUND_SOURCE_CHOICES,
        default="CDRRMO Fund",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.vehicle:
            if not self.vehicle_name:
                self.vehicle_name = self.vehicle.vehicle_name
            if not self.plate_no:
                self.plate_no = self.vehicle.plate_no
            if not self.vehicle_type:
                self.vehicle_type = self.vehicle.vehicle_type
            if not self.section:
                self.section = self.vehicle.section

        self.amount = Decimal(str(self.amount)).quantize(Decimal("0.01"))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle_name} - {self.product} - {self.date}"


class SystemSettings(models.Model):
    system_name = models.CharField(max_length=150, blank=True, default="")
    office_name = models.CharField(max_length=150, blank=True, default="")
    admin_name = models.CharField(max_length=150, blank=True, default="")
    admin_email = models.EmailField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.system_name or "System Settings"


class AdminAccount(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username