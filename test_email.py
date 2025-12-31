#!/usr/bin/env python
"""
Test email configuration for Railway deployment
Run this to verify email settings work correctly
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sportclub.settings')
django.setup()

from django.core.mail import send_mail
from django.test import TestCase

def test_email_configuration():
    """Test if email configuration works"""
    try:
        print("Testing email configuration...")
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        
        # Send test email
        result = send_mail(
            subject='Test Email from Railway',
            message='This is a test email to verify configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself
            fail_silently=False,
        )
        
        if result:
            print("✅ Email sent successfully!")
            return True
        else:
            print("❌ Email failed to send")
            return False
            
    except Exception as e:
        print(f"❌ Email configuration error: {str(e)}")
        return False

if __name__ == "__main__":
    test_email_configuration()