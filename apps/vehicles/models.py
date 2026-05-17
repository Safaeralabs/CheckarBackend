from django.db import models

from apps.common.models import SoftDeleteModel


class FuelTypeChoices(models.TextChoices):
    GASOLINE = "gasoline", "Gasolina"
    DIESEL = "diesel", "Diesel"
    HYBRID = "hybrid", "Hibrido"
    ELECTRIC = "electric", "Electrico"
    GAS = "gas", "Gas"


class VehicleTypeChoices(models.TextChoices):
    LIGHT = "light", "Liviano"
    HEAVY = "heavy", "Pesado"
    MOTORCYCLE = "motorcycle", "Motocicleta"


class VehicleClassChoices(models.TextChoices):
    AUTO = "auto", "Automovil"
    PICKUP = "pickup", "Camioneta"
    SUV = "suv", "Campero"
    VAN = "van", "Microbus / Van"
    TRUCK = "truck", "Camion"
    BUS = "bus", "Bus"
    MOTORCYCLE = "motorcycle", "Motocicleta"
    OTHER = "other", "Otro"


class ServiceCategoryChoices(models.TextChoices):
    PARTICULAR = "particular", "Particular"
    COMMERCIAL = "commercial", "Comercial"
    PUBLIC = "public", "Publico"


class Vehicle(SoftDeleteModel):
    owner = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="vehicles")
    plate = models.CharField(max_length=10, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VehicleTypeChoices.choices)
    vehicle_class = models.CharField(max_length=20, choices=VehicleClassChoices.choices, blank=True)
    service_category = models.CharField(
        max_length=20, choices=ServiceCategoryChoices.choices, default=ServiceCategoryChoices.PARTICULAR
    )
    brand = models.CharField(max_length=80)
    model_line = models.CharField(max_length=120)
    model_year = models.PositiveIntegerField()
    color = models.CharField(max_length=40, blank=True)
    fuel_type = models.CharField(max_length=20, choices=FuelTypeChoices.choices)
    vin = models.CharField(max_length=50, blank=True)
    engine_number = models.CharField(max_length=50, blank=True)
    mileage = models.PositiveIntegerField(default=0)
    num_axes = models.PositiveSmallIntegerField(default=2)
    num_passengers = models.PositiveSmallIntegerField(null=True, blank=True)
    displacement = models.PositiveIntegerField(null=True, blank=True, help_text="Cilindraje en cc")
    registration_city = models.CharField(max_length=120, blank=True, help_text="Ciudad de matrícula del vehículo")
    tinted_windows = models.BooleanField(default=False)
    armored = models.BooleanField(default=False)
    non_functional = models.BooleanField(default=False)

    def __str__(self):
        return self.plate
