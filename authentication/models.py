from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser
from authentication.managers import MyUserManager, CompanyManager
import pytz

RIYADH_TZ = pytz.timezone("Asia/Riyadh")

class BaseModel(models.Model):
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    objects = CompanyManager()

    def save(self, *args, **kwargs):
        now = timezone.now().astimezone(RIYADH_TZ)

        if not self.created_at:
            self.created_at = now
        self.updated_at = now

        super().save(*args, **kwargs)

class PermissionModel(models.Model):
    is_temperature = models.BooleanField(default=False)  # temperature
    is_guard = models.BooleanField(default=False)  # guard
    is_peoplecount = models.BooleanField(default=False)  # headcount
    is_kitchen = models.BooleanField(default=False)  # kitchen
    is_foodweight = models.BooleanField(default=False)  # weight
    is_cleanness = models.BooleanField(default=False)  # cleaness
    is_buffet = models.BooleanField(default=False)  # buffet
    is_cleaners = models.BooleanField(default=False)  # clearners
    is_sentiment = models.BooleanField(default=False)  # sentiment
    is_water_tank = models.BooleanField(default=False)  # water_sensor, water_tank
    is_sensor_assign = models.BooleanField(default=False)
    is_annotator_ranking = models.BooleanField(default=False)
    is_settings = models.BooleanField(default=False)

    class Meta:
        abstract = True

class Company(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    name_ar = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    icon = models.ImageField(upload_to='company_fav_icon/', null=True, blank=True)
    def __str__(self):
        return self.name

class MyUser(AbstractBaseUser):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name="users")
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30, null=False, blank=False)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_annotator = models.BooleanField(default=False)
    company_annotator = models.ManyToManyField(Company, blank=True)
    sensor_update_permission = models.BooleanField(default=False)
    assigned_office = models.ManyToManyField('office.Office', blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = MyUserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return True