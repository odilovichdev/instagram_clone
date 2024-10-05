import uuid
from datetime import datetime, timedelta
import random

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from shared.models import BaseModel


class User(AbstractUser, BaseModel):
    class UserType(models.TextChoices):
        ADMIN = "ADMIN", _("Admin")
        MANAGER = "MANAGER", _("Manager")
        ORDINARY_USER = "ORDINARY_USER", _("Ordinary user")

    class AuthType(models.TextChoices):
        VIA_EMAIL = "VIA_EMAIL", _("Via email")
        VIA_PHONE = "VIA_PHONE", _("Via phone")

    class AuthStatus(models.TextChoices):
        NEW = "NEW", _("New")
        VERIFY_CODE = "VERIFY_CODE", _("Verify code")
        DONE = "DONE", _("Done")
        PHOTO_STEP = "PHOTO_STEP", _("Photo step")

    class Gender(models.TextChoices):
        MALE = "MALE", _("Male")
        FEMALE = "FEMALE", _("Female")

    user_type = models.CharField(max_length=13, choices=UserType, default=UserType.ORDINARY_USER)
    auth_type = models.CharField(max_length=9, choices=AuthType)
    auth_status = models.CharField(max_length=11, choices=AuthStatus, default=AuthStatus.NEW)
    gender = models.CharField(max_length=6, choices=Gender)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    image = models.ImageField(upload_to='users/', null=True, blank=True,
                              validators=[FileExtensionValidator(
                                  allowed_extensions=['jpeg', 'jpg', 'png','heic', 'heif']
                              )]
                              )

    def __str__(self):
        return self.username

    def create_verify_type(self, verify_type):
        code = "".join([str(random.randint(0, 100) % 10) for _ in range(4)])
        UserConfirmation.objects.create(
            user_id=self.pk,
            verify_type=verify_type,
            code=code
        )
        return code

    def check_username(self):
        if not self.username:
            temp_username = f"instagram-{uuid.uuid4().__str__().split('-')[-1]}"
            while User.objects.filter(username=temp_username).exists():# ToDo exists ning vazifasini tekshir
                temp_username = f"{temp_username}{random.randint(0, 9)}"

            self.username = temp_username

    def check_email(self):
        if self.email:
            normalize_email = self.email.lower()
            self.email = normalize_email

    def check_pass(self):
        if not self.password:
            temp_password = f"password-{uuid.uuid4().__str__().split('-')[-1]}"
            self.password = temp_password

    def hashing_password(self):
        if not self.password.startswith('pbkdf2_sha256'):
            self.set_password(self.password)

    def token(self):
        refresh = RefreshToken.for_user(self)
        return {
            'access': str(refresh.access_token),
            'refresh_toekn': str(refresh)
        }

    def clean(self):
        self.check_email()
        self.check_pass()
        self.check_username()
        self.hashing_password()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.clean()
        super(User, self).save(*args, **kwargs)


EXPIRE_EMAIL = 5
EXPIRE_PHONE = 2


class UserConfirmation(BaseModel):
    class VerifyType(models.TextChoices):
        VIA_EMAIL = "VIA_EMAIL", _("Via email")
        VIA_PHONE = "VIA_PHONE", _("Via Phone")

    code = models.CharField(max_length=4)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='verify_codes')
    verify_type = models.CharField(max_length=9, choices=VerifyType)
    expiration_time = models.DateTimeField(null=True)
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user.__str__())

    def save(self, *args, **kwargs):
        # TODO shu funksiyani tekshir
        if not self.pk:
            if self.verify_type == self.VerifyType.VIA_EMAIL:
                self.expiration_time = datetime.now() + timedelta(minutes=EXPIRE_EMAIL)
            else:
                self.expiration_time = datetime.now() + timedelta(minutes=EXPIRE_PHONE)

        super(UserConfirmation, self).save(*args, **kwargs)
