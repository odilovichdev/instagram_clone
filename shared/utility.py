import re

from rest_framework.exceptions import ValidationError

email_regex = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

phone_regex = re.compile(
    r'^(\+\d{1,3})?\s?\(?\d{1,4}\)?[\s.-]?\d{3}[\s.-]?\d{4}$'
)


def check_email_or_phone_number(email_or_phone):
    if re.fullmatch(email_regex, email_or_phone):
        email_or_phone = 'email'
    elif re.fullmatch(phone_regex, email_or_phone):
        email_or_phone = 'phone'
    else:
        raise ValidationError(
            {
                "success": False,
                "message": "Email yoki telefon raqamingiz noto'g'ri"
            }
        )
    return email_or_phone
