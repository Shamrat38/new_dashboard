from django.urls import path, include
from .views import DashboardIllegalPilgrims
urlpatterns = [
    path('dashboard/', DashboardIllegalPilgrims.as_view()),
]
