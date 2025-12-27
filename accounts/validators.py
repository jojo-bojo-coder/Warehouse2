"""
Backend validation functions for Sign In
Add these functions to your views.py or create a separate validators.py file
"""

import re
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


def validate_signin_credentials(email_or_username, password):
    """
    Validate signin credentials and return validation errors

    Args:
        email_or_username (str): Email address or username
        password (str): User password

    Returns:
        dict: Dictionary containing 'valid' boolean and 'errors' dict
    """
    errors = {}

    # Validate email/username
    if not email_or_username:
        errors['email'] = "البريد الإلكتروني أو اسم المستخدم مطلوب"
    elif len(email_or_username.strip()) < 3:
        errors['email'] = "يجب أن يكون 3 أحرف على الأقل"

    # Validate password
    if not password:
        errors['password'] = "كلمة المرور مطلوبة"
    elif len(password) < 4:
        errors['password'] = "كلمة المرور قصيرة جداً"

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def sanitize_signin_input(email_or_username):
    """
    Sanitize and normalize signin input

    Args:
        email_or_username (str): Email address or username

    Returns:
        str: Sanitized input
    """
    if not email_or_username:
        return ''

    # Strip whitespace and convert to lowercase
    sanitized = email_or_username.strip().lower()

    # Remove any potentially harmful characters
    sanitized = re.sub(r'[<>\"\'\\]', '', sanitized)

    return sanitized


def find_user_by_credentials(email_or_username):
    """
    Find user by email or username

    Args:
        email_or_username (str): Email address or username

    Returns:
        User: User object if found, None otherwise
    """
    if not email_or_username:
        return None

    # Try to find by email first
    user = User.objects.filter(email=email_or_username).first()

    # If not found, try by username
    if not user:
        user = User.objects.filter(username=email_or_username).first()

    return user


def validate_recaptcha(recaptcha_response, secret_key):
    """
    Validate reCAPTCHA response

    Args:
        recaptcha_response (str): reCAPTCHA response token
        secret_key (str): reCAPTCHA secret key

    Returns:
        dict: Dictionary containing 'valid' boolean and 'error' message
    """
    import requests

    if not recaptcha_response:
        return {
            'valid': False,
            'error': 'الرجاء إكمال التحقق من reCAPTCHA'
        }

    try:
        data = {
            'secret': secret_key,
            'response': recaptcha_response
        }

        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data, timeout=5)
        result = r.json()

        if result.get('success'):
            return {
                'valid': True,
                'error': None
            }
        else:
            return {
                'valid': False,
                'error': 'فشل التحقق من reCAPTCHA. يرجى المحاولة مرة أخرى'
            }
    except requests.exceptions.RequestException:
        return {
            'valid': False,
            'error': 'خطأ في الاتصال بخدمة reCAPTCHA'
        }
    except Exception as e:
        return {
            'valid': False,
            'error': f'خطأ غير متوقع: {str(e)}'
        }


def check_account_status(user):
    """
    Check if user account is active and not locked

    Args:
        user (User): Django User object

    Returns:
        dict: Dictionary containing 'valid' boolean and 'error' message
    """
    if not user:
        return {
            'valid': False,
            'error': 'المستخدم غير موجود'
        }

    if not user.is_active:
        return {
            'valid': False,
            'error': 'الحساب غير نشط. يرجى التواصل مع الدعم'
        }

    # Add additional checks here (e.g., account locked, suspended, etc.)
    # Example:
    # if hasattr(user, 'profile') and user.profile.is_locked:
    #     return {
    #         'valid': False,
    #         'error': 'الحساب مقفل. يرجى التواصل مع الدعم'
    #     }

    return {
        'valid': True,
        'error': None
    }


def log_failed_login_attempt(email_or_username, ip_address, user_agent):
    """
    Log failed login attempts for security monitoring

    Args:
        email_or_username (str): Email or username attempted
        ip_address (str): IP address of the request
        user_agent (str): User agent string
    """
    # Implement logging logic here
    # You can store in database, log file, or send alerts
    import logging

    logger = logging.getLogger('security')
    logger.warning(
        f"Failed login attempt - User: {email_or_username}, "
        f"IP: {ip_address}, User-Agent: {user_agent}"
    )


def get_client_ip(request):
    """
    Get client IP address from request

    Args:
        request: Django request object

    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

