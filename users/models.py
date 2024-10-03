import random
import uuid
from datetime import datetime, timedelta

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from shared.models import BaseModel


class User(AbstractUser, BaseModel):
    class USER_TYPE(models.TextChoices):
        ADMIN = "ADMIN", _("Admin")
        MANAGER = "MANAGER", _("Manager")
        ORDINARY_USER = "ORDINARY_USER", _("Ordinary_user")

    class AUTH_TYPE(models.TextChoices):
        EMAIL = "EMAIL", _("Email")
        PHONE = "PHONE", _("Phone")

    class AUTH_STATUS(models.TextChoices):
        NEW = "NEW", _("New")
        VERIFIED_CODE = "VERIFIED_CODE", _("Verified_code")
        DONE = "DONE", _("Done")
        PHOTO_STEP = "PHONE_STEP", _("Photo_step")

    class GENDER(models.TextChoices):
        MALE = "MALE", _("Male")
        FEMALE = "FEMALE", _("Female")
        OPTIONAL = "OPTIONAL", _("Optional")

    user_type = models.CharField(max_length=13, choices=USER_TYPE, default=USER_TYPE.ORDINARY_USER)
    auth_type = models.CharField(max_length=5, choices=AUTH_TYPE)
    auth_status = models.CharField(max_length=13, choices=AUTH_STATUS)
    gender = models.CharField(max_length=8, choices=GENDER)
    email = models.EmailField(null=True, blank=True, unique=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True, unique=True)
    images = models.ImageField(upload_to='users/', null=True, blank=True,
                               validators=[FileExtensionValidator(
                                   allowed_extensions=['jpg', 'jpeg', 'png', 'heic', 'heif']
                               )]
                               )

    def __str__(self):
        return self.username

    def create_verify_type(self, verify_type):
        code = "".join([str(random.randint(0, 100) % 10) for _ in range(4)])
        UserConfirmation.objects.create(
            user_id=self.id,
            verify_type=verify_type,
            code=code
        )
        return code

    def check_username(self):
        if self.username:
            temp_username = f"instagram-{uuid.uuid4().__str__().split('-')[-1]}"
            while User.objects.filter(username=temp_username):
                temp_username = f"{temp_username}{random.randint(0, 9)}"

            self.username = temp_username

    def check_email(self):
        if self.email:
            normalize_email = self.email.lower()
            self.email = normalize_email

    def check_pass(self):
        if not self.password:
            temp_password = f"instagram-{uuid.uuid4().__str__().split()[-1]}"
            self.password = temp_password

    def hashing_password(self):
        if not self.password.startswith('pbkdf2_sha256'):
            self.set_password(self.password)

    def token(self):
        refresh = RefreshToken.for_user(self)
        return {
            'access': str(refresh.access_token),
            'refresh_token': str(refresh)
        }

    def clean(self):
        self.check_email()
        self.check_username()
        self.check_pass()
        self.hashing_password()

    def save(self, *args, **kwargs):
        if self.pk:
            self.clean()
        super(User, self).save(*args, **kwargs)


PHONE_EXPIRE = 2
EMAIL_EXPIRE = 5


class UserConfirmation(BaseModel):
    class VERIFY_TYPE(models.TextChoices):
        EMAIL = "EMAIL", _("Email")
        PHONE = "PHONE", _("Phone")

    code = models.CharField(max_length=4)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='verify_codes')
    verify_type = models.CharField(max_length=5, choices=VERIFY_TYPE)
    expiration_time = models.DateTimeField(null=True)
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user.__str__())

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.verify_type == self.VERIFY_TYPE.EMAIL:
                self.expiration_time = datetime.now() + timedelta(minutes=EMAIL_EXPIRE)
            else:
                self.expiration_time = datetime.now() + timedelta(minutes=PHONE_EXPIRE)

        super(UserConfirmation, self).save(*args, **kwargs)
