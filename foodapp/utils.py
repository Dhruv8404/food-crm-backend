import random
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import OTP

def generate_otp():
    return ''.join(str(random.randint(0, 9)) for _ in range(6))

def send_otp_email(email):
    otp = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=5)

    OTP.objects.filter(email=email).delete()
    OTP.objects.create(email=email, otp=otp, expires_at=expires_at)

    send_mail(
        subject="Your OTP Code",
        message=f"Your OTP is {otp}. It will expire in 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

def verify_otp(email, otp):
    try:
        record = OTP.objects.get(email=email, otp=otp)
        if record.expires_at < timezone.now():
            record.delete()
            return False, "OTP expired"

        record.delete()  # ✅ IMPORTANT
        return True, "OTP verified"

    except OTP.DoesNotExist:
        return False, "Invalid OTP"
