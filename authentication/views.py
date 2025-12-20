from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
import pytz
from django.utils import timezone

from authentication.models import MyUser, Company
from authentication.serializers import UserRegistrationSerializer, UserLoginSerializer, MyUserSerializer
from authentication.utils import standard_response, get_token_for_user


saudi_tz = pytz.timezone('Asia/Riyadh')


def Current_saudi_time():
    now_saudi = timezone.now().astimezone(saudi_tz)
    start_time = saudi_tz.localize(
        datetime.combine(now_saudi.date(), time.min))
    end_time = now_saudi

    return start_time, end_time
class CustomPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Allow clients to set their own page size
    max_page_size = 100  # Limit the maximum page size

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


@method_decorator(csrf_exempt, name='dispatch')
class UserView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = MyUserSerializer

    def get(self, request, *args, **kwargs):
        queryset = MyUser.objects.filter(
            company=request.user.company
        ).order_by('id')

        paginate = request.query_params.get(
            'paginate', 'true').lower() == 'true'

        if paginate:
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(
                queryset, request, view=self)
            serializer = self.serializer_class(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True)
        return Response({
            "success": True,
            "message": "User list retrieved successfully without pagination.",
            "data": serializer.data
        })

    def delete(self, request, pk, *args, **kwargs):
        try:
            user = MyUser.objects.get(id=pk)
            if user.company != request.user.company:
                return Response({
                    "success": False,
                    "message": f"User with ID {pk} does not belong to your company."
                }, status=403)

            user.delete()
            return Response({
                "success": True,
                "message": f"User with ID {pk} deleted successfully."
            }, status=200)

        except MyUser.DoesNotExist:
            return Response({
                "success": False,
                "message": f"User with ID {pk} not found."
            }, status=404)

    def patch(self, request, pk, *args, **kwargs):
        try:
            user = MyUser.objects.get(id=pk)
            if user.company != request.user.company:
                return Response({
                    "success": False,
                    "message": f"User with ID {pk} does not belong to your company."
                }, status=403)

            serializer = UserRegistrationSerializer(
                user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(company=request.user.company)

            return Response({
                "success": True,
                "message": f"User with ID {pk} updated successfully.",
                "results": serializer.data
            }, status=200)

        except MyUser.DoesNotExist:
            return Response({
                "success": False,
                "message": f"User with ID {pk} not found."
            }, status=404)
            
            
class ServerTime(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_time, end_time = Current_saudi_time()
        return Response({"server_time": end_time.isoformat()})