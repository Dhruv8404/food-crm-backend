import random
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import OTP

# Email configuration is handled in Django settings

def generate_otp(length=6):
    """Generate a random numeric OTP."""
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def send_otp_email(email):
    """Send OTP to the specified email address."""
    otp = generate_otp()
    expiry = timezone.now() + timedelta(minutes=5)

    # Save OTP to DB
    OTP.objects.filter(email=email).delete()  # Remove old OTPs for this email
    otp_obj = OTP.objects.create(email=email, otp=otp, expires_at=expiry)

    subject = "Your OTP Code"
    message = f"""
Hello,

Your OTP is: {otp}

It will expire in 5 minutes.

Best regards,
Your OTP Verification System
"""

    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        print(f"✅ OTP sent successfully to {email}: {otp}")
        return True, "OTP sent successfully."
    except Exception as e:
        otp_obj.delete()  # Clean up if sending failed
        print(f"❌ Error sending email: {e}")
        return False, f"Error sending email: {str(e)}"

def verify_otp(email, entered_otp):
    """Verify the entered OTP."""
    try:
        otp_obj = OTP.objects.filter(email=email).latest('created_at')
        if otp_obj.is_expired():
            otp_obj.delete()
            return False, "OTP expired."
        if otp_obj.otp != entered_otp:
            return False, "Invalid OTP."
        # Don't delete OTP immediately to allow for retries
        return True, "OTP verified successfully."
    except OTP.DoesNotExist:
        return False, "No OTP found for this email."

def send_bill_email_util(email, bill_details):
    """Send bill details to the specified email address."""
    subject = "Your Bill Details"

    try:
        send_mail(
            subject,
            bill_details,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        print(f"✅ Bill sent successfully to {email}")
        return True, "Bill sent successfully."
    except Exception as e:
        print(f"❌ Error sending bill email: {e}")
        return False, f"Error sending email: {str(e)}"
