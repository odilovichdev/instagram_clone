from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.validators import FileExtensionValidator
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken

from shared.utility import check_email_or_phone_number, send_email, check_user_type
from users.models import User


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(
            required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'auth_type',
            'auth_status',
        )

        extra_kwargs = {
            'auth_type': {"read_only": True, "required": False},
            'auth_status': {"read_only": True, "required": False}
        }

    def create(self, validated_data):
        user = super(SignUpSerializer, self).create(validated_data)
        # user -> email -> email jo'natish kk
        # user -> phone -> telefoniga kod ni jo'natish kk
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
        user.save()
        return user

    def validate(self, data):
        super(SignUpSerializer, self).validate(data)
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        user_input = str(data.get('email_phone_number')).lower()
        input_type = check_email_or_phone_number(user_input)
        if input_type == 'email':
            data = {
                'email': user_input,
                'auth_type': User.AuthType.VIA_EMAIL,
            }
        elif input_type == 'phone':
            data = {
                'phone_number': user_input,
                'auth_type': User.AuthType.VIA_PHONE,
            }
        else:
            raise ValidationError(
                {
                    'status': False,
                    'message': 'You must send email or phone number'
                }
            )
        return data

    def validate_email_phone_number(self, value):
        value = value.lower()
        # ToDo
        if value and User.objects.filter(email=value).exists():
            raise ValidationError(
                {
                    "success": False,
                    "message": "Bu email oldin yaratilgan!"
                }
            )
        elif value and User.objects.filter(phone_number=value).exists():
            raise ValidationError(
                {
                    "success": False,
                    "message": "Bu raqam oldin ro'yhatdan o'tgan!"
                }
            )
        return value

    def to_representation(self, instance):
        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())
        return data


class ChangeUserInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(write_only=True, required=True)
    last_name = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        password = attrs.get('password', None)
        confirm_password = attrs.get('confirm_password', None)
        first_name = attrs.get('first_name', None)
        last_name = attrs.get('last_name', None)
        username = attrs.get("username", None)

        if password != confirm_password:
            raise ValidationError(
                {
                    "message": "Parolingiz va tasdiqlash parolingiz bir-biriga teng emas!"
                }
            )
        if password:
            validate_password(password)

        if first_name is not None:
            self.check(first_name)
        if last_name is not None:
            self.check(last_name)
        if username is not None:
            self.check(username)

        return attrs

    @staticmethod
    def check(data):
        if 5 > len(data) or len(data) > 30:
            raise ValidationError(
                {
                    "message": f"{data.capitalize()} must be 5 and 30 characters long"
                }
            )
        if data.isdigit():
            raise ValidationError(
                {
                    "message": f"This {data} is entirely numeric"
                }
            )
        return data

    def update(self, instance: User, validated_data):
        instance.first_name = validated_data.get(
            'first_name', instance.first_name)
        instance.last_name = validated_data.get(
            'last_name', instance.last_name)
        instance.password = validated_data.get('password', instance.password)
        instance.username = validated_data.get('username', instance.username)

        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))

        if instance.auth_status == User.AuthStatus.VERIFY_CODE:
            instance.auth_status = User.AuthStatus.DONE

        instance.save()
        return instance


class ChangeUserPhotoSerializer(serializers.Serializer):
    image = serializers.ImageField(validators=[
        FileExtensionValidator(allowed_extensions=[
            'jpg', 'jpeg', 'png', 'heic', 'heif'
        ])
    ])

    def update(self, instance: User, validated_data):
        image = validated_data.get("image")
        if image is not None:
            instance.image = validated_data.get("image", instance.image)
            instance.auth_status = User.AuthStatus.PHOTO_DONE
        instance.save()
        return instance


class LoginSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.fields['user_input'] = serializers.CharField(required=True)
        self.fields['username'] = serializers.CharField(required=False, read_only=True)

    def auth_validate(self, data):
        user_input = data.get('user_input')  # email, phone, username
        auth_type = check_user_type(user_input)
        if auth_type == 'username':
            username = user_input
        elif auth_type == 'email':
            user = self.get_user(email__iexact=user_input)
            username = user.username
        elif auth_type == 'phone':
            user = self.get_user(phone_number=user_input)
            username = user.username
        else:
            raise ValidationError(
                {
                    "success": False,
                    'message': "Email, username yoki nomer kiritishingiz kerak"
                }
            )
        authentication_kwargs = {
            self.username_field: username,
            'password': data['password'],
        }
        # user statusini tekshiramiz

        current_user = User.objects.filter(username__iexact=username).first()
        if current_user is not None and current_user.auth_status in [User.AuthStatus.NEW, User.AuthStatus.VERIFY_CODE]:
            raise ValidationError(
                {
                    "Success": False,
                    "message": "Siz ro'yhatdan to'liq o'tmagansiz"
                }
            )

        user = authenticate(**authentication_kwargs)

        if user is not None:
            self.user = user
        else:
            raise ValidationError(
                {
                    "success": False,
                    "message": "Sorry, login or username you entered is incorrect. Please check and try again"
                }
            )

    def validate(self, data):
        self.auth_validate(data)
        if self.user.auth_status not in [User.AuthStatus.DONE, User.AuthStatus.PHOTO_DONE]:
            raise PermissionDenied(
                "Siz login qila olmaysiz, ruxsatingiz yo'q!"
            )
        data = self.user.token()
        data['auth_status'] = self.user.auth_status
        data['full_name '] = self.user.get_full_name()
        return data

    def get_user(self, **kwargs):
        users = User.objects.filter(**kwargs)
        if not users.exists():
            raise ValidationError(
                {
                    "No active account found"
                }
            )
        return users.first()


class LoginRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super(LoginRefreshSerializer, self).validate(attrs)
        access_token_instance = AccessToken(data['access'])
        user_id = access_token_instance['user_id']
        user = get_object_or_404(User, id=user_id)
        update_last_login(None, user)
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgetPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email_or_phone = attrs.get("email_or_phone", None)

        if email_or_phone is None:
            raise ValidationError(
                {
                    "success": False,
                    "message": "Email yoki nomer kiritilishi shart"
                }
            )

        user = User.objects.filter(Q(phone_number__iexact=email_or_phone) | Q(email__iexact=email_or_phone))

        if not user.exists():
            raise NotFound("User not fount")
        attrs['user'] = user.first()

        return attrs


class ResetPasswordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "password",
            "confirm_password",
        )

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if password != confirm_password:
            raise ValidationError(
                {
                    "success": False,
                    "message": "Parollar bir-xil bo'lishi kerak"
                }
            )

        if password is not None:
            validate_password(password)

        return attrs

    def update(self, instance: User, validated_data):
        password = validated_data.pop("password")
        instance.set_password(password)
        return super(ResetPasswordSerializer, self).update(instance, validated_data)
