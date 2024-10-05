from rest_framework import permissions
from rest_framework.generics import CreateAPIView

from users.models import User
from users.serializers import SignUpSerializer


class CreateUserAPIView(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = SignUpSerializer
