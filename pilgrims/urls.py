from django.urls import path, include
from .views import CameraCounterView, RFIDCounterView, IlligalPilgrimsView, get_pilgrims_statistics_for_tent
urlpatterns = [
    path('camera-counter/', CameraCounterView.as_view()),
    path('rfid-counter/', RFIDCounterView.as_view()),
    path('illigal-pilgrims/', IlligalPilgrimsView.as_view()),
    path('illegal-pilgrims/<int:pk>', IlligalPilgrimsView.as_view()),
    path('<int:tent_id>/pilgrim_statistics/',
         get_pilgrims_statistics_for_tent, name='camera_statistics'),
    path('<int:tent_id>/pilgrim_statistics/<str:date>/',
         get_pilgrims_statistics_for_tent, name='camera_statistics_by_date'),
]
