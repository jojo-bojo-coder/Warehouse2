from django.db import models
from accounts.models import ClubsModel


class ClubSecuritySettings(models.Model):
    """Model for storing club security settings"""
    club = models.OneToOneField(
        ClubsModel,
        on_delete=models.CASCADE,
        related_name='security_settings'
    )
    enable_otp_verification = models.BooleanField(
        default=True,
        verbose_name="تفعيل التحقق بخطوتين (OTP)"
    )
    enable_recaptcha = models.BooleanField(
        default=True,
        verbose_name="تفعيل reCAPTCHA"
    )
    otp_method = models.CharField(
        max_length=20,
        choices=[
            ('whatsapp', 'واتساب'),
            ('email', 'البريد الإلكتروني'),
            ('both', 'كليهما')
        ],
        default='both',
        verbose_name="طريقة إرسال OTP"
    )
    otp_expiry_minutes = models.PositiveIntegerField(
        default=5,
        verbose_name="مدة صلاحية OTP (دقائق)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "إعدادات الأمان للنادي"
        verbose_name_plural = "إعدادات الأمان للأندية"

    def __str__(self):
        return f"إعدادات الأمان - {self.club.name}"

    @classmethod
    def get_or_create_for_club(cls, club):
        """Get or create security settings for a club"""
        settings, created = cls.objects.get_or_create(
            club=club,
            defaults={
                'enable_otp_verification': True,
                'enable_recaptcha': True,
                'otp_method': 'both',
                'otp_expiry_minutes': 5
            }
        )
        return settings
