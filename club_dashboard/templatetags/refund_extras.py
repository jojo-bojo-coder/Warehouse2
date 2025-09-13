from django import template
from django.utils.translation import get_language

register = template.Library()


@register.filter
def refund_status_display(status, language_code=None):
    """Display refund status in appropriate language"""
    if not language_code:
        language_code = get_language()

    status_dict = {
        'pending': {'ar': 'قيد مراجعة البائع', 'en': 'Pending Vendor Review'},
        'coach_rejected': {'ar': 'مرفوض من قبل البائع', 'en': 'Rejected by Vendor'},
        'escalated': {'ar': 'تم تصعيده إلى المسؤول', 'en': 'Escalated to Admin'},
        'investigating': {'ar': 'قيد التحقيق', 'en': 'Under Investigation'},
        'approved': {'ar': 'تم الموافقة', 'en': 'Approved'},
        'rejected': {'ar': 'مرفوض', 'en': 'Rejected'},
        'resolved': {'ar': 'تم الحل', 'en': 'Resolved'},
        'canceled': {'ar': 'ملغي', 'en': 'Canceled'},
    }

    return status_dict.get(status, {}).get(language_code, status)


@register.filter
def dispute_type_display(dispute_type, language_code=None):
    """Display dispute type in appropriate language"""
    if not language_code:
        language_code = get_language()

    type_dict = {
        'quality': {'ar': 'مشكلة في الجودة', 'en': 'Quality Issue'},
        'service_not_provided': {'ar': 'خدمة غير مقدمة', 'en': 'Service Not Provided'},
        'delivery_delay': {'ar': 'تأخر في التسليم', 'en': 'Delivery Delay'},
        'wrong_item': {'ar': 'عنصر/خدمة خاطئة', 'en': 'Wrong Item/Service'},
        'damage': {'ar': 'عنصر تالف', 'en': 'Damaged Item'},
        'billing_error': {'ar': 'خطأ في الفاتورة', 'en': 'Billing Error'},
        'other': {'ar': 'أخرى', 'en': 'Other'},
    }

    return type_dict.get(dispute_type, {}).get(language_code, dispute_type)


@register.filter
def priority_display(priority, language_code=None):
    """Display priority in appropriate language"""
    if not language_code:
        language_code = get_language()

    priority_dict = {
        'low': {'ar': 'منخفض', 'en': 'Low'},
        'medium': {'ar': 'متوسط', 'en': 'Medium'},
        'high': {'ar': 'عالي', 'en': 'High'},
        'urgent': {'ar': 'عاجل', 'en': 'Urgent'},
    }

    return priority_dict.get(priority, {}).get(language_code, priority)