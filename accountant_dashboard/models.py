from django.db import models

class VATSettings(models.Model):
    CURRENCY_CHOICES = [
        ('ر.س', 'ر.س - Saudi Riyal'),
        ('$', '$ - US Dollar'),
        ('€', '€ - Euro'),
        ('£', '£ - British Pound'),
        ('د.إ', 'د.إ - UAE Dirham'),
        ('د.ك', 'د.ك - Kuwaiti Dinar'),
        ('د.ب', 'د.ب - Bahraini Dinar'),
        ('ر.ق', 'ر.ق - Qatari Riyal'),
        ('ر.ع', 'ر.ع - Omani Rial'),
        ('د.ا', 'د.ا - Algerian Dinar'),
        ('د.م', 'د.م - Moroccan Dirham'),
        ('ج.م', 'ج.م - Egyptian Pound'),
        ('ل.ل', 'ل.ل - Lebanese Pound'),
        ('ل.س', 'ل.س - Syrian Pound'),
        ('د.ع', 'د.ع - Iraqi Dinar'),
        ('ر.ي', 'ر.ي - Yemeni Rial'),
        ('د.ت', 'د.ت - Tunisian Dinar'),
        ('د.ل', 'د.ل - Libyan Dinar'),
        ('ج.س', 'ج.س - Sudanese Pound'),
    ]
    club = models.OneToOneField('accounts.ClubsModel', on_delete=models.CASCADE, related_name='vat_settings')
    language = models.CharField(
        max_length=10,
        choices=[('ar', 'Arabic'), ('en', 'English')],
        default='ar',
        verbose_name="Language"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    currency = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        default='ر.س',
        verbose_name="العملة"
    )

    class Meta:
        verbose_name = "VAT Setting"
        verbose_name_plural = "VAT Settings"

    def __str__(self):
        return f"VAT Settings for {self.club.name}"


from django.db import models
from accounts.models import UserProfile


class BillRevision(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Accountant Review'),
        ('accountant_reviewed', 'Accountant Reviewed'),
        ('director_reviewed', 'Director Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    order = models.ForeignKey('students.Order', on_delete=models.CASCADE, related_name='bill_revisions')
    accountant = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True,
                                   related_name='accountant_revisions')
    director = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='director_revisions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    accountant_notes = models.TextField(blank=True, null=True)
    director_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bill Revision"
        verbose_name_plural = "Bill Revisions"

    def __str__(self):
        return f"Revision for Order #{self.order.id} - {self.get_status_display()}"


class BillRevisionComment(models.Model):
    revision = models.ForeignKey(BillRevision, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.revision}"



from django.db import models
from accounts.models import ClubsModel

class Banner(models.Model):
    club = models.ForeignKey(ClubsModel, on_delete=models.CASCADE, related_name='banners')
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='banners/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']




class LandingPageContent(models.Model):
    club = models.OneToOneField('accounts.ClubsModel', on_delete=models.CASCADE, related_name='landing_page_content')
    hero_title = models.CharField(max_length=200)
    hero_subtitle = models.CharField(max_length=200)
    about_title = models.CharField(max_length=200)
    about_description = models.TextField()
    features_title = models.CharField(max_length=200)
    plans_title = models.CharField(max_length=200)
    cta_title = models.CharField(max_length=200)
    cta_description = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Landing Page Content for {self.club.name}"

class TermsAndConditions(models.Model):
    club = models.OneToOneField('accounts.ClubsModel', on_delete=models.CASCADE, related_name='terms_and_conditions')
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Terms & Conditions for {self.club.name}"
