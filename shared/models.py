import uuid

from django.db import models


class BaseModel(models.Model):
    id = models.URLField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
