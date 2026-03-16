import re
from rest_framework import serializers
from .models import Vehicle, FuelTransaction, BudgetAllocation, SystemSettings


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
        read_only_fields = ("amount", "created_at")
        extra_kwargs = {
            "vehicle_name": {"required": False, "allow_blank": True},
            "vehicle_type": {"required": False},
            "section": {"required": False},
            "plate_no": {"required": False, "allow_blank": True, "allow_null": True},
            "destination": {"required": False, "allow_blank": True, "allow_null": True},
            "odometer": {"required": False, "allow_blank": True, "allow_null": True},
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

    def validate(self, attrs):
        vehicle = attrs.get("vehicle", getattr(self.instance, "vehicle", None))
        vehicle_name = attrs.get(
            "vehicle_name",
            getattr(self.instance, "vehicle_name", None),
        )

        if not vehicle and not str(vehicle_name or "").strip():
            raise serializers.ValidationError(
                {"vehicle_name": "Select a vehicle or enter a vehicle/equipment name."}
            )

        return attrs

    def create(self, validated_data):
        vehicle = validated_data.get("vehicle")

        if vehicle:
            validated_data.setdefault("vehicle_name", vehicle.vehicle_name)
            validated_data.setdefault("plate_no", vehicle.plate_no)
            validated_data.setdefault("vehicle_type", vehicle.vehicle_type)
            validated_data.setdefault("section", vehicle.section)

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