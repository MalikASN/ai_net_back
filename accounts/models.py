# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, EmailValidator
from django.db import models


username_validator = RegexValidator(
regex=r'^[a-zA-Z0-9_]{3,30}$',
message='Username must be 3–30 chars, letters/digits/underscore only.'
)


class User(AbstractUser):
    # Override username to enforce our regex
    username = models.CharField(
    max_length=30,
    unique=True,
    validators=[username_validator],
    )
    # Ensure unique email with validation
    email = models.EmailField(
    unique=True,
    validators=[EmailValidator(message='Enter a valid email address.')]
    )

    def __str__(self):
      return self.username
    
