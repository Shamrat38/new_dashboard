from django.urls import path, include
from .views import OfficeApiView
urlpatterns = [
    path('', OfficeApiView.as_view()),
    #path('dashboard/', DashboardIllegalPilgrims.as_view()),
]
