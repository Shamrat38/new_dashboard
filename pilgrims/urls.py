from django.urls import path, include
from .views import CameraCounterView, RFIDCounterView, IlligalPilgrimsView
urlpatterns = [
    path('camera-counter/', CameraCounterView.as_view()),
    path('rfid-counter/', RFIDCounterView.as_view()),
    path('illigal-pilgrims/', IlligalPilgrimsView.as_view()),
    path('illegal-pilgrims/<int:pk>', IlligalPilgrimsView.as_view()),
]
