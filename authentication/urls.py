from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from authentication.views import UserRegistrationView, UserLoginView, UserView, ServerTime, CompanyWithLogo

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path("users/", UserView.as_view()),
    path("users/<int:pk>/", UserView.as_view()),
    path('token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('time/', ServerTime.as_view()),
    path('company-logo/', CompanyWithLogo.as_view()),
]