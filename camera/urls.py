from django.urls import path, include
from camera.views import PeopleCountingCardView, PeopleGraphView
urlpatterns = [
    path('people-counter/', PeopleCountingCardView.as_view()),
    path('people-counter-graph/', PeopleGraphView.as_view()),
]
