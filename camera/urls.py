from django.urls import path, include
from camera.views import CreateCounterHistory, PeopleCountingCardView, PeopleGraphView
urlpatterns = [
    path('create-counter-history/', CreateCounterHistory.as_view()),
    path('people-counter/', PeopleCountingCardView.as_view()),
    path('people-counter-graph/', PeopleGraphView.as_view()),
]
