from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    VehicleViewSet,
    FuelTransactionViewSet,
    BudgetAllocationViewSet,
    dashboard_summary,
    login_view,
    system_settings_view,
    change_password_view,
)

router = DefaultRouter()
router.register(r"vehicles", VehicleViewSet, basename="vehicle")
router.register(r"fuel-transactions", FuelTransactionViewSet, basename="fuel-transaction")
router.register(r"budgets", BudgetAllocationViewSet, basename="budget")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard-summary/", dashboard_summary, name="dashboard-summary"),
    path("auth/login/", login_view, name="auth-login"),
    path("auth/change-password/", change_password_view, name="auth-change-password"),
    path("system-settings/", system_settings_view, name="system-settings"),
]