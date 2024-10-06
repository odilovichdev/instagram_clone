from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from shared.utility import check_email_or_phone_number, send_email
from users.models import User


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(required=False)

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
            # send_phone_code(user.phone_number, code)
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
        print('to_rep', instance)
        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())
        return data
