from django.contrib.auth.models import AbstractBaseUser, AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Creates and returns a user with an email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Set the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Creates and returns a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class UserProfile(AbstractUser):
    username = None  # Remove username as we will use email for login
    email = models.EmailField(unique=True)  # Set email as the unique identifier
    
    objects = CustomUserManager()

    height_cm = models.FloatField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')
    ], null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    target_weight_kg = models.FloatField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    activity_level = models.CharField(max_length=20, choices=[
        ('Sedentary', 'Sedentary'), ('Lightly active', 'Lightly active'),
        ('Moderately active', 'Moderately active'), ('Very active', 'Very active')
    ], null=True, blank=True)
    join_date = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'  # Set email as the username field
    REQUIRED_FIELDS = []  # No additional required fields

    def __str__(self):
        return self.email