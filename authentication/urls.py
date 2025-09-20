from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from authentication.views import UserRegistrationView, UserLoginView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('token-refresh/', TokenRefreshView.as_view(), name='token_refresh')
]