from django.urls import path, include
from .views import CameraCounterView, RFIDCounterView
urlpatterns = [
    path('camera-counter/', CameraCounterView.as_view()),
    path('rfid-counter/', RFIDCounterView.as_view()),
]
