import re
import threading

import phonenumbers
from decouple import config
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError
from twilio.rest import Client

email_regex = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

phone_regex = re.compile(
    r'^(\+\d{1,3})?\s?\(?\d{1,4}\)?[\s.-]?\d{3}[\s.-]?\d{4}$'
)

username_regex = re.compile(
    r"[a-zA-Z0-9]+(._)?"
)


def check_user_type(user_input):
    if re.fullmatch(email_regex, user_input):
        user_input = 'email'
    elif re.fullmatch(phone_regex, user_input):
        user_input = 'phone'
    elif re.fullmatch(username_regex, user_input):
        user_input = 'username'
    else:
        raise ValidationError(
            {
                "status": False,
                "message": "Email, username yoki telefon nomer xato kiritildi"
            }
        )
    return user_input


def check_email_or_phone_number(email_or_phone):
    phone_number = phonenumbers.parse(email_or_phone)
    if re.fullmatch(email_regex, email_or_phone):
        email_or_phone = 'email'
    elif phonenumbers.is_valid_number(phone_number):
        email_or_phone = 'phone'
    else:
        raise ValidationError(
            {
                "success": False,
                "message": "Email yoki telefon raqamingiz noto'g'ri"
            }
        )
    return email_or_phone


class EmailTread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


class Email:
    @staticmethod
    def send_email(data):  # ToDo staticmethod ni o'rganish
        email = EmailMessage(
            subject=data['subject'],
            body=data['body'],
            to=[data['to_email']],
        )
        if data.get('content-type') == 'html':
            email.content_subtype = 'html'
        EmailTread(email).start()  # ToDo thread larni o'rganish


def send_email(email, code):
    html_content = render_to_string(
        'email/authentication/activate_account.html',
        {'code': code}
    )
    Email.send_email(
        {
            "subject": "Ro'yhatdan o'tish",
            "to_email": email,
            'body': html_content,
            'content_type': 'html',
        }
    )


def send_phone_code(phone, code):
    account_sid = config('account_sig')
    auth_token = config("auth_token")
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=f"Salom, sizning tasdiqlash kodingiz {code}",
        from_="+998907205768",
        to=f"{phone}",
    )
