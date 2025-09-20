from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import GenericAPIView

from authentication.serializers import UserRegistrationSerializer, UserLoginSerializer
from authentication.utils import standard_response

@method_decorator(csrf_exempt, name='dispatch')
class UserRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(company=request.user.company)
            return Response(*standard_response(True, 'User registered successfully.', serializer.data, status.HTTP_201_CREATED))
        else:
            return Response(*standard_response(False, 'Validation failed.', serializer.errors, status.HTTP_400_BAD_REQUEST))


@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        return Response(*standard_response(True, 'User logged in successfully.', {
            'token': get_token_for_user(user),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
        }))
