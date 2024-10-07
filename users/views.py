from datetime import datetime

from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.utility import send_email
from users.models import User
from users.serializers import SignUpSerializer


class CreateUserAPIView(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = SignUpSerializer


class VerifyAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        code = self.request.data.get('code')

        self.check_verify(user, code)
        return Response(data={
            "success": True,
            "auth_status": user.auth_status,
            "access": user.token()['access'],
            "refresh": user.token()["refresh_token"]
        }
        )

    @staticmethod
    def check_verify(user: User, code):
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), code=code, is_confirmed=False)
        if not verifies.exists():
            raise ValidationError(
                {
                    "status": False,
                    "message": "Tasdiqlash kodingiz xato yoki eskirgan"
                }
            )
        verifies.update(is_confirmed=True)
        if user.auth_status == User.AuthStatus.NEW:
            user.auth_status = User.AuthStatus.VERIFY_CODE
            user.save()
        return True


class GetNewVerificationAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = self.request.user
        self.check_verification(user)
        send_code_email_or_phone(user)
        return Response(
            data={
                "success": True,
                "message": "Tasdiqlash kodingiz qaytadan yuborildi"
            }
        )

    @staticmethod
    def check_verification(user: User):
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), is_confirmed=False)
        if verifies.exists():
            raise ValidationError(
                {
                    "message": "Kodingiz hali ishlatish uchun yqroqli biroz kutib turing!"
                }
            )
        return True

def send_code_email_or_phone(user: User):
    if user.auth_type == User.AuthType.VIA_EMAIL:
        code = user.create_verify_type(User.AuthType.VIA_EMAIL)
        send_email(user.email, code)
    elif user.auth_type == User.AuthType.VIA_PHONE:
        code = user.create_verify_type(User.AuthType.VIA_PHONE)
        send_email(user.phone_number, code)
    else:
        raise ValidationError(
            {
                "message": "Email yoki telefon raqami noto'g'ri"
            }
        )


