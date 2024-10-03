from datetime import datetime, timedelta
import random

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

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
    auth_type = models.CharField(max_length=5, choices=AUTH_TYPE, default=AUTH_TYPE.EMAIL)
    auth_status = models.CharField(max_length=13, choices=AUTH_STATUS, default=AUTH_STATUS.NEW)
    gender = models.CharField(max_length=8, choices=GENDER, default=GENDER.OPTIONAL)
    email = models.EmailField(null=True, blank=True, unique=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True, unique=True)
    images = models.ImageField(upload_to='users/', null=True, blank=True,
                               validators=[FileExtensionValidator(
                                   allowed_extensions=['jpg', 'jpeg', 'png', 'heic', 'heif']
                               )]
                               )

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def create_verify_type(self, verify_type):
        code = "".join([str(random.randint(0, 100) % 10) for _ in range(4)])
        UserConfirmation.objects.create(
            user_id=self.id,
            verify_type=verify_type,
            code=code
        )
        return code


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
