import re
from decimal import Decimal
from rest_framework import serializers

from .models import (
    Vehicle,
    FuelTransaction,
    BudgetAllocation,
    SystemSettings,
)


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = "__all__"


class BudgetAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetAllocation
        fields = "__all__"


class FuelTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelTransaction
        fields = "__all__"
        read_only_fields = ("created_at",)
        extra_kwargs = {
            "vehicle_name": {"required": False, "allow_blank": True},
            "vehicle_type": {"required": False},
            "section": {"required": False},
            "plate_no": {"required": False, "allow_blank": True, "allow_null": True},
            "destination": {"required": False, "allow_blank": True, "allow_null": True},
            "odometer": {"required": False, "allow_blank": True, "allow_null": True},
            "fund_year": {"required": False},
        }

    def validate_odometer(self, value):
        if value in (None, ""):
            return value

        value = str(value).strip()

        if not re.fullmatch(r"\d+(\s*-\s*\d+)?", value):
            raise serializers.ValidationError(
                "Odometer must be a number or a range like 130-143."
            )

        if "-" in value:
            start_str, end_str = [part.strip() for part in value.split("-", 1)]
            start = int(start_str)
            end = int(end_str)

            if end < start:
                raise serializers.ValidationError(
                    "The second odometer value must be greater than or equal to the first value."
                )

            return f"{start}-{end}"

        return str(int(value))

    def validate_fund_year(self, value):
        if value in (None, ""):
            return 2026

        try:
            value = int(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Fund year must be a valid year.")

        allowed_years = [2025, 2026, 2027, 2028, 2029, 2030]

        if value not in allowed_years:
            raise serializers.ValidationError(
                "Fund year must be between 2025 and 2030."
            )

        return value

    def _validate_decimals(self, value, field_name, label, max_decimals):
        if value in (None, ""):
            return value

        value_str = str(value).strip()

        if "." in value_str:
            decimal_part = value_str.split(".", 1)[1]

            if len(decimal_part) > max_decimals:
                raise serializers.ValidationError(
                    {
                        field_name: f"{label} must have at most {max_decimals} decimal places."
                    }
                )

        return value

    def validate(self, attrs):
        vehicle = attrs.get("vehicle", getattr(self.instance, "vehicle", None))
        vehicle_name = attrs.get(
            "vehicle_name",
            getattr(self.instance, "vehicle_name", None),
        )

        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))
        unit_price = attrs.get("unit_price", getattr(self.instance, "unit_price", None))
        amount = attrs.get("amount", getattr(self.instance, "amount", None))
        fund_year = attrs.get("fund_year", getattr(self.instance, "fund_year", 2026))

        if not vehicle and not str(vehicle_name or "").strip():
            raise serializers.ValidationError(
                {
                    "vehicle_name": "Select a vehicle or enter a vehicle/equipment name."
                }
            )

        self._validate_decimals(quantity, "quantity", "Quantity", 3)
        self._validate_decimals(unit_price, "unit_price", "Unit price", 2)
        self._validate_decimals(amount, "amount", "Amount", 2)

        if quantity is None or Decimal(str(quantity)) <= 0:
            raise serializers.ValidationError(
                {"quantity": "Quantity must be greater than 0."}
            )

        if unit_price is None or Decimal(str(unit_price)) <= 0:
            raise serializers.ValidationError(
                {"unit_price": "Unit price must be greater than 0."}
            )

        if amount is None or Decimal(str(amount)) <= 0:
            raise serializers.ValidationError(
                {"amount": "Amount must be greater than 0."}
            )

        try:
            fund_year = int(fund_year)
        except (TypeError, ValueError):
            raise serializers.ValidationError(
                {"fund_year": "Fund year must be a valid year."}
            )

        allowed_years = [2025, 2026, 2027, 2028, 2029, 2030]

        if fund_year not in allowed_years:
            raise serializers.ValidationError(
                {"fund_year": "Fund year must be between 2025 and 2030."}
            )

        attrs["fund_year"] = fund_year
        attrs["amount"] = Decimal(str(amount)).quantize(Decimal("0.01"))

        return attrs

    def create(self, validated_data):
        vehicle = validated_data.get("vehicle")

        if vehicle:
            validated_data.setdefault("vehicle_name", vehicle.vehicle_name)
            validated_data.setdefault("plate_no", vehicle.plate_no)
            validated_data.setdefault("vehicle_type", vehicle.vehicle_type)
            validated_data.setdefault("section", vehicle.section)

        validated_data.setdefault("fund_year", 2026)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        vehicle = validated_data.get("vehicle", instance.vehicle)

        if vehicle:
            validated_data.setdefault("vehicle_name", vehicle.vehicle_name)
            validated_data.setdefault("plate_no", vehicle.plate_no)
            validated_data.setdefault("vehicle_type", vehicle.vehicle_type)
            validated_data.setdefault("section", vehicle.section)

        return super().update(instance, validated_data)


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = "__all__"