from django.contrib.auth import get_user_model
from rest_framework import serializers
from authentication.models import MyUser

from office.models import Office

class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(
        style={"input_type": "password"}, write_only=True)
    office_list = serializers.CharField(required=False)

    class Meta:
        model = MyUser
        fields = ["email", "username", "password", "password2", "tent_list", "company", "is_temperature", "is_guard",
                  "is_peoplecount", "is_kitchen", "is_foodweight", "is_cleanness",
                  "is_buffet", "is_cleaners", "is_sentiment", "is_water_tank"]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"validators": []},
            "company": {"required": False},
        }

    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError(
                {"password": "Password and Confirm Password are not match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        office_list = validated_data.pop('tent_list', None)
        company = validated_data.pop('company', None)

        # Extract permission fields separately
        permission_fields = {
            'is_temperature': validated_data.pop('is_temperature', False),
            'is_guard': validated_data.pop('is_guard', False),
            'is_peoplecount': validated_data.pop('is_peoplecount', False),
            'is_kitchen': validated_data.pop('is_kitchen', False),
            'is_foodweight': validated_data.pop('is_foodweight', False),
            'is_cleanness': validated_data.pop('is_cleanness', False),
            'is_buffet': validated_data.pop('is_buffet', False),
            'is_cleaners': validated_data.pop('is_cleaners', False),
            'is_sentiment': validated_data.pop('is_sentiment', False),
            'is_water_tank': validated_data.pop('is_water_tank', False),
        }

        # Create the user
        user = MyUser.objects.create_user(**validated_data)

        # Assign permissions
        for field, value in permission_fields.items():
            setattr(user, field, value)

        # Assign the Company instance
        if company:
            user.company = company

        # Handle assigned_office (ManyToMany)
        if office_list:
            try:
                office_ids = [int(id.strip()) for id in office_list.split(",")]
                offices = Office.objects.filter(id__in=office_ids)
                user.assigned_tent.set(offices)
            except:
                raise serializers.ValidationError("Invalid Office list")

        user.save()
        return user

    def update(self, instance, validated_data):
        # Extract non-model fields from validated_data
        office_list = validated_data.pop('office_list', None)
        company = validated_data.pop('company', None)

        # Update core fields using parent implementation
        user = super().update(instance, validated_data)

        # Update ManyToMany: assigned_tent
        user.assigned_tent.clear()
        if office_list:
            try:
                office_ids = [int(id.strip()) for id in office_list.split(",")]
                offices = Office.objects.filter(id__in=office_ids)
                user.assigned_office.set(offices)
            except (ValueError, Office.DoesNotExist):
                raise serializers.ValidationError(
                    {"tent_list": "Invalid tent IDs provided"})
        user.save()
        return user
    
class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        style={'input_type': 'password'}, write_only=True, required=True)

    class Meta:
        model = get_user_model()
        fields = ('email', 'password')

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Check for required fields
        if not email:
            raise serializers.ValidationError({"email": "Email is required."})
        if not password:
            raise serializers.ValidationError(
                {"password": "Password is required."})

        User = get_user_model()
        try:
            user = MyUser.objects.get(email=email)
        except MyUser.DoesNotExist:
            raise serializers.ValidationError(
                {"user": "User with this Email does not exist."})

        if not user.check_password(password):
            raise serializers.ValidationError({"invalid": "Invalid password."})

        attrs['user'] = user
        return attrs