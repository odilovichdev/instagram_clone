from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from shared.utility import send_email, check_email_or_phone_number
from users.models import User
from users.serializers import SignUpSerializer, ChangeUserInfoSerializer, ChangeUserPhotoSerializer, LoginSerializer, \
    LoginRefreshSerializer, LogoutSerializer, ForgetPasswordSerializer, ResetPasswordSerializer


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


class ChangeUserInfoAPIView(UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChangeUserInfoSerializer
    http_method_names = ['put', 'patch']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super(ChangeUserInfoAPIView, self).update(request, *args, **kwargs)

        return Response(
            {
                "success": True,
                "message": "User updated successfully",
                "auth_status": self.request.user.auth_status,
            },
            status=200
        )

    def partial_update(self, request, *args, **kwargs):
        super(ChangeUserInfoAPIView, self).partial_update(request, *args, **kwargs)

        return Response(
            {
                "success": True,
                "message": "User updated successfully",
                "auth_status": self.request.user.auth_status,
            },
            status=200
        )


class ChangeUserImageAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        serializer = ChangeUserPhotoSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            user = request.user
            serializer.update(user, serializer.validated_data)
            return Response(
                {
                    "message": "Rasm muvaffaqiyatli o'zgartirildi!"
                },
                status=200
            )
        return Response(
            serializer.errors, status=400
        )


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class LoginRefreshView(TokenRefreshView):
    serializer_class = LoginRefreshSerializer


class LogOutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_classes(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = self.request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(data={
                "success": True,
                "message": "You are logged out"
            }, status=205)
        except TokenError:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ForgetPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ForgetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        email_or_phone = serializer.validated_data.get('email_or_phone')
        user = serializer.validated_data.get("user")

        if check_email_or_phone_number(email_or_phone) == 'phone':
            code = user.create_verify_type(User.AuthType.VIA_PHONE)
            send_email(email_or_phone, code)
        elif check_email_or_phone_number(email_or_phone) == 'email':
            code = user.create_verify_type(User.AuthType.VIA_EMAIL)
            send_email(email_or_phone, code)

        return Response(
            {
                "status": True,
                "message": "Kod yuborildi",
                "access": user.token()['access'],
                "refresh_token": user.token()['refresh_token'],
                "auth_status": user.auth_status
            },
            status=200
        )


class ResetPasswordView(UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ResetPasswordSerializer
    http_method_names = ['put', 'patch']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super(ResetPasswordView, self).update(request, *args, **kwargs)
        try:
            user = User.objects.get(id=response.data.get('id'))
        except ObjectDoesNotExist as e:
            raise NotFound(detail="User not found")

        return Response(
            {
                "success": True,
                "message": "Password muvaffaqiyatli o'zgartirildi",
                "access": user.token()['access'],
                "refresh_token": user.token()['refresh_token'],
                "auth_type": user.auth_type
            }
        )
