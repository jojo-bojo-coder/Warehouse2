from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import ClubsModel, UserProfile
from students.models import Order
from django.utils.timezone import now  # ✅ Import existing ClubsModel
from accounts.models import StudentProfile, CoachProfile  # ✅ Import the correct models




try:
    from students.models import ProductsModel  # ✅ Import ProductsModel safely
except ImportError:
    ProductsModel = None  # ✅ Prevents ImportError in circular dependencies


# ✅ Model for tracking product stockx`
class ProductsStockModel(models.Model):
    product = models.ForeignKey(
        'students.ProductsModel',
        on_delete=models.CASCADE,
        related_name="stock_entries",
        verbose_name="المنتج"
    )
    quantity = models.PositiveIntegerField(verbose_name="الكمية المتاحة")
    creation_date = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")  # ✅ Added tracking for updates

    def __str__(self):
        return f"{self.product.name} - Stock: {self.quantity}"

class ProductImg(models.Model):
    product = models.ForeignKey('students.ProductsModel', on_delete=models.CASCADE, related_name='product_images')
    img = models.ImageField(upload_to='product_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'

    def __str__(self):
        return f"Image for {self.product.name}"


# ✅ Model for club-wide notifications
class Notification(models.Model):
    club = models.ForeignKey(
        ClubsModel,  # ✅ Correct reference to ClubsModel from accounts
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="النادي"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # ✅ Prevents issues when a user is deleted
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name="المستخدم"
    )
    message = models.TextField(verbose_name="الرسالة")
    is_read = models.BooleanField(default=False, verbose_name="تم القراءة")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")  # ✅ Added for tracking notification updates

    def __str__(self):
        return f"Notification for {self.user.username if self.user else 'Unknown'}: {self.message[:50]}..."
        
        
class Review(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="student_reviews")
    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name="coach_reviews")
    rating = models.IntegerField(choices=[(i, f"{i}⭐") for i in range(1, 6)], default=5)
    comment = models.TextField(null=True, blank=True)  # ✅ Allows NULL values to prevent migration errors
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.student.full_name} for {self.coach.full_name} ({self.rating}/5)"


class SalonAppointment(models.Model):
    DAY_CHOICES = [
        ('السبت', 'السبت'),
        ('الأحد', 'الأحد'),
        ('الإثنين', 'الإثنين'),
        ('الثلاثاء', 'الثلاثاء'),
        ('الأربعاء', 'الأربعاء'),
        ('الخميس', 'الخميس'),
        ('الجمعة', 'الجمعة'),
    ]
    club = models.ForeignKey(
        ClubsModel,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name="النادي"
    )
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    is_paid = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        status = "متاح" if self.available else "محجوز"
        time_display = f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}" if self.start_time and self.end_time else "N/A"
        return f"{self.day} - {time_display} ({status})- {self.club.name}"



class ProductShipment(models.Model):
    product = models.ForeignKey(
        'students.ProductsModel',
        on_delete=models.CASCADE,
        related_name='shipments',
        verbose_name="المنتج"
    )
    quantity = models.PositiveIntegerField(verbose_name="الكمية")
    manufacturing_date = models.DateField(null=True, blank=True, verbose_name="تاريخ التصنيع")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="تاريخ انتهاء الصلاحية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    def save(self, *args, **kwargs):
        # Check if this is a new shipment (not an update)
        is_new = self.pk is None

        # Call the original save method first
        super().save(*args, **kwargs)

        # If this is a new shipment, update the product stock
        if is_new:
            self.product.stock += self.quantity
            self.product.save()

    def delete(self, *args, **kwargs):
        # Reduce the product stock when a shipment is deleted
        self.product.stock -= self.quantity
        self.product.save()
        super().delete(*args, **kwargs)

    @property
    def is_expiring_soon(self):
        if not self.expiration_date:
            return False

        import datetime
        one_month_later = datetime.date.today() + datetime.timedelta(days=30)
        return self.expiration_date <= one_month_later and self.expiration_date > datetime.date.today()

    @property
    def is_expired(self):
        if not self.expiration_date:
            return False

        import datetime
        return self.expiration_date < datetime.date.today()

    @property
    def remaining_quantity(self):
        return self.quantity

    def __str__(self):
        return f"شحنة {self.product.title} - {self.quantity} وحدة - تاريخ الإنتهاء: {self.expiration_date or 'غير محدد'}"

    class Meta:
        ordering = ['expiration_date', 'created_at']
        verbose_name = "شحنة منتج"
        verbose_name_plural = "شحنات المنتجات"

@property
def get_order_type(self):
    """Returns the type of the order: products, services, or mixed"""
    has_products = self.items.filter(product__isnull=False).exists()
    has_services = self.items.filter(service__isnull=False).exists()

    if has_products and has_services:
        return 'mixed'
    elif has_products:
        return 'products'
    elif has_services:
        return 'services'
    else:
        return 'unknown'

@property
def get_order_type_display(self):
    """Returns the display name for the order type in Arabic"""
    order_type = self.get_order_type
    if order_type == 'products':
        return 'منتجات'
    elif order_type == 'services':
        return 'خدمات'
    elif order_type == 'mixed':
        return 'منتجات وخدمات'
    else:
        return 'غير معروف'


class DashboardSettings(models.Model):
    show_employee_client_counts = models.BooleanField(
        default=True,
        verbose_name="Show Employee & Client Counts",
        help_text="Toggle visibility of employee and client count cards on student dashboard"
    )

    class Meta:
        verbose_name = "Dashboard Settings"
        verbose_name_plural = "Dashboard Settings"

    def __str__(self):
        return f"Dashboard Settings - Counts: {'Visible' if self.show_employee_client_counts else 'Hidden'}"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and DashboardSettings.objects.exists():
            raise ValueError("Dashboard Settings already exists. Only one instance is allowed.")
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create dashboard settings instance"""
        settings, created = cls.objects.get_or_create(
            id=1,
            defaults={'show_employee_client_counts': True}
        )
        return settings



from django.utils.text import slugify
class Category(models.Model):
    name_en = models.CharField(max_length=100, verbose_name='English Name')
    name_ar = models.CharField(max_length=100, verbose_name='Arabic Name')
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Use English name for slug generation
            self.slug = slugify(self.name_en)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name_en

    @property
    def name(self):
        """Return the appropriate name based on current language"""
        from django.utils import translation
        if translation.get_language() == 'ar' and self.name_ar:
            return self.name_ar
        return self.name_en

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class SubCategory(models.Model):
    """
    SubCategory model for more detailed product organization
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories'
    )
    name_en = models.CharField(max_length=100, verbose_name='English Name')
    name_ar = models.CharField(max_length=100, verbose_name='Arabic Name')
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='subcategories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Use English name for slug generation
            self.slug = slugify(self.name_en)
        super(SubCategory, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name_en} - {self.name_en}"

    @property
    def name(self):
        """Return the appropriate name based on current language"""
        from django.utils import translation
        if translation.get_language() == 'ar' and self.name_ar:
            return self.name_ar
        return self.name_en

    class Meta:
        verbose_name = 'SubCategory'
        verbose_name_plural = 'SubCategories'
        unique_together = ('category', 'name_en', 'name_ar')



from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
def get_commission_types():
    language = get_language()
    if language == 'ar':
        return [
            ('vendor', 'عمولة البائع'),
            ('time_period', 'عرض لفترة زمنية'),
        ]
    else:
        return [
            ('vendor', "Vendor's commission"),
            ('time_period', "Time period offer"),
        ]
class Commission(models.Model):
    COMMISSION_TYPE_CHOICES = [
        ('vendor', 'Vendor Commission'),
        ('time_period', 'Time Period Offer'),
    ]

    COMMISSION_TYPE_CHOICES_AR = [
        ('vendor', 'عمولة البائع'),
        ('time_period', 'عرض لفترة زمنية'),
    ]
    vendor_classification = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default='silver',
        verbose_name="تصنيف البائع"
    )

    # Basic fields
    name = models.CharField(max_length=100, verbose_name="اسم العمولة")
    commission_type = models.CharField(
        max_length=20,
        choices=COMMISSION_TYPE_CHOICES,  # استخدام الخيارات الإنجليزية كافتراضي
        verbose_name=_("Commission Type")
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="نسبة العمولة (%)"
    )

    # Time period fields ( represents discount period)
    start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ بداية العرض"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ نهاية العرض"
    )

    # discount amount (only for time_period type)
    discount_amount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True,
        null=True,
        verbose_name="مقدار الخصم (%)",
        help_text="سيتم خصم هذه النسبة من جميع العمولات خلال هذه الفترة"
    )

    # Status and metadata
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    club = models.ForeignKey(
        'accounts.ClubsModel',
        on_delete=models.CASCADE,
        verbose_name="النادي"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="تم الإنشاء بواسطة"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    @classmethod
    def get_commission_choices(cls):
        """دالة مساعدة للحصول على الخيارات"""
        language = get_language()
        if language == 'ar':
            return cls.COMMISSION_TYPE_CHOICES_AR
        else:
            return cls.COMMISSION_TYPE_CHOICES

    @classmethod
    def get_commission_choices_with_all(cls):
        """Return choices including 'All Types' option"""
        choices = cls.get_commission_choices()
        language = get_language()

        if language == 'ar':
            all_types_option = ('', 'جميع الأنواع')
        else:
            all_types_option = ('', 'All Types')

        return [all_types_option] + choices

    class Meta:
        verbose_name = "عمولة"
        verbose_name_plural = "العمولات"
        ordering = ['-created_at']

    def __str__(self):
        if self.commission_type == 'vendor':
            return f"{self.name} - {self.vendor_classification} - {self.commission_rate}%"
        else:
            return f"{self.name} - {self.start_date} إلى {self.end_date} - {self.commission_rate}%"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.commission_type == 'vendor':
            if not self.vendor_classification:
                raise ValidationError('تصنيف البائع مطلوب لعمولة البائع')
            self.vendor_classification = self.vendor_classification.strip().lower()
            if self.start_date or self.end_date or self.discount_amount:
                raise ValidationError('حقول الفترة الزمنية والخصم غير مطلوبة لعمولة البائع')

        # Validate time period offer
        elif self.commission_type == 'time_period':
            if not self.start_date or not self.end_date:
                raise ValidationError('تاريخ البداية والنهاية مطلوبان للخصم الزمني')
            if self.start_date >= self.end_date:
                raise ValidationError('تاريخ البداية يجب أن يكون قبل تاريخ النهاية')
            if not self.discount_amount:
                raise ValidationError('مقدار الخصم مطلوب للخصم الزمني')
            if self.discount_amount < 0 or self.discount_amount > 100:
                raise ValidationError('مقدار الخصم يجب أن يكون بين 0 و 100')
            if self.vendor_classification:
                raise ValidationError('تصنيف البائع غير مطلوب للخصم الزمني')

    def save(self, *args, **kwargs):
        self.full_clean()
        # Ensure the choice is valid
        valid_choices = [choice[0] for choice in self.get_commission_choices()]
        if self.commission_type not in valid_choices:
            raise ValueError("Invalid commission type")
        super().save(*args, **kwargs)

    @classmethod
    def get_vendor_commission(cls, club, vendor_profile=None):
        """Get the appropriate commission for a vendor"""
        # Get all active vendor commissions for the club
        vendor_commissions = cls.objects.filter(
            club=club,
            commission_type='vendor',
            is_active=True
        ).order_by('-commission_rate')

        if not vendor_commissions.exists():
            # Create default silver commission if none exists
            default_commission = cls.objects.create(
                name="عمولة فضية افتراضية",
                commission_type='vendor',
                commission_rate=18.00,
                vendor_classification='silver',
                club=club,
                is_active=True
            )
            return default_commission

        # If vendor already has a classification, use it
        if vendor_profile and hasattr(vendor_profile, 'vendor_classification'):
            vendor_commission = vendor_commissions.filter(
                vendor_classification=vendor_profile.vendor_classification
            ).first()
            if vendor_commission:
                return vendor_commission

        # For new vendors, assign the highest commission available
        return vendor_commissions.first()

    @classmethod
    def get_time_period_commission(cls, club, date=None):
        """Get active time period discount for a specific date"""
        if date is None:
            date = timezone.now().date()

        return cls.objects.filter(
            club=club,
            commission_type='time_period',
            is_active=True,
            start_date__lte=date,
            end_date__gte=date
        ).first()

    @classmethod
    def get_effective_rate(cls, vendor_commission, date=None):
        """
        Calculate the effective rate after applying any active time period discounts
        """
        if date is None:
            date = timezone.now().date()

        # Get active time period discount
        discount = cls.objects.filter(
            club=vendor_commission.club,
            commission_type='time_period',
            is_active=True,
            start_date__lte=date,
            end_date__gte=date
        ).first()

        if discount:
            effective_rate = vendor_commission.commission_rate - discount.discount_amount
            return max(effective_rate, 0)  # Ensure rate doesn't go below 0

        return vendor_commission.commission_rate

    @classmethod
    def get_available_classifications(cls, club):
        """Get all unique vendor classifications for a club"""
        return cls.objects.filter(
            club=club,
            commission_type='vendor',
            is_active=True
        ).values_list('vendor_classification', flat=True).distinct()

    @cached_property
    def commission_type_choices(self):
        """إرجاع الخيارات بناءً على اللغة الحالية"""
        language = get_language()
        if language == 'ar':
            return self.COMMISSION_TYPE_CHOICES_AR
        else:
            return self.COMMISSION_TYPE_CHOICES


class VendorCommissionAssignment(models.Model):
    """Track commission assignments to vendors"""
    vendor = models.OneToOneField(
        'accounts.CoachProfile',
        on_delete=models.CASCADE,
        verbose_name="البائع",
        related_name='commission_assignment'
    )
    commission = models.ForeignKey(
        Commission,
        on_delete=models.CASCADE,
        verbose_name="العمولة"
    )
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التخصيص")

    class Meta:
        verbose_name = "تخصيص عمولة البائع"
        verbose_name_plural = "تخصيصات عمولة البائعين"

    def __str__(self):
        return f"{self.vendor.full_name} - {self.commission.name}"



from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


class RefundStatus(models.TextChoices):
    """Status options for a refund/dispute"""
    PENDING = 'pending', _('Pending Vendor Review')
    COACH_REJECTED = 'coach_rejected', _('Rejected by Vendor')
    ESCALATED = 'escalated', _('Escalated to Admin')
    INVESTIGATING = 'investigating', _('Under Investigation')
    APPROVED = 'approved', _('Approved')
    REJECTED = 'rejected', _('Rejected')
    RESOLVED = 'resolved', _('Resolved')
    CANCELED = 'canceled', _('Canceled')

    def get_display(self, language_code):
        """Get display text based on language"""
        if language_code == 'ar':
            arabic_translations = {
                'pending': 'قيد مراجعة البائع',
                'coach_rejected': 'مرفوض من قبل البائع',
                'escalated': 'تم تصعيده إلى المسؤول',
                'investigating': 'قيد التحقيق',
                'approved': 'تم الموافقة',
                'rejected': 'مرفوض',
                'resolved': 'تم الحل',
                'canceled': 'ملغي'
            }
            return arabic_translations.get(self.value, self.label)
        return self.label


class RefundType(models.TextChoices):
    """Type of refund"""
    FULL = 'full', _('Full Refund')
    PARTIAL = 'partial', _('Partial Refund')


from django.db import models
from django.utils import timezone
from datetime import timedelta

class RefundDisputeMessage(models.Model):
    """Model for storing messages in a refund dispute conversation"""
    dispute = models.ForeignKey('RefundDispute', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('accounts.UserProfile', on_delete=models.CASCADE)
    message = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message {self.id} in Dispute {self.dispute.id}"


class DisputeType(models.TextChoices):
    """Type of dispute"""
    QUALITY_ISSUE = 'quality', _('Quality Issue')
    SERVICE_NOT_PROVIDED = 'service_not_provided', _('Service Not Provided')
    DELIVERY_DELAY = 'delivery_delay', _('Delivery Delay')
    WRONG_ITEM = 'wrong_item', _('Wrong Item/Service')
    DAMAGE = 'damage', _('Damaged Item')
    BILLING_ERROR = 'billing_error', _('Billing Error')
    OTHER = 'other', _('Other')

    def get_display(self, language_code):
        """Get display text based on language"""
        if language_code == 'ar':
            arabic_translations = {
                'quality': 'مشكلة في الجودة',
                'service_not_provided': 'خدمة غير مقدمة',
                'delivery_delay': 'تأخر في التسليم',
                'wrong_item': 'عنصر/خدمة خاطئة',
                'damage': 'عنصر تالف',
                'billing_error': 'خطأ في الفاتورة',
                'other': 'أخرى'
            }
            return arabic_translations.get(self.value, self.label)
        return self.label


class RefundDispute(models.Model):
    """
    Model representing refunds and disputes between clients and vendors
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(help_text=_('Detailed description of the issue'))

    # Related deal
    deal = models.ForeignKey(
        'students.Order',
        on_delete=models.CASCADE,
        related_name='refund_disputes',
        verbose_name='Order'
    )

    # Parties involved
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_refund_disputes',
        editable=False  # Make this non-editable in admin
    )
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_refund_disputes',
        editable=False  # Make this non-editable in admin
    )

    current_stage = models.CharField(
        max_length=20,
        choices=[
            ('student_coach', 'Student-Coach Discussion'),
            ('receptionist', 'Receptionist Review'),
            ('director', 'Director Review'),
            ('resolved', 'Resolved')
        ],
        default='student_coach'
    )

    last_message_time = models.DateTimeField(auto_now_add=True)
    stage_start_time = models.DateTimeField(auto_now_add=True)
    next_escalation_time = models.DateTimeField(null=True, blank=True)

    # Refund details
    refund_type = models.CharField(
        max_length=20,
        choices=RefundType.choices,
        default=RefundType.FULL
    )
    dispute_type = models.CharField(
        max_length=30,
        choices=DisputeType.choices,
        default=DisputeType.OTHER
    )

    # Financial details
    original_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_('Original deal amount')
    )
    requested_refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_('Amount requested for refund')
    )
    currency = models.CharField(max_length=10, default='USD')

    # Admin decision
    approved_refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Final approved refund amount')
    )
    vendor_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True,
        help_text=_('Percentage of refund amount vendor will receive')
    )
    client_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True,
        help_text=_('Percentage of refund amount client will receive')
    )

    # Calculated amounts (auto-populated)
    vendor_refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Amount vendor will receive')
    )
    client_refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Amount client will receive')
    )

    is_escalated = models.BooleanField(default=False, help_text="Whether dispute has been escalated to club admin")
    coach_notes = models.TextField(blank=True, null=True, help_text="Coach's notes about the dispute")

    # Status and review
    status = models.CharField(
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_refund_disputes'
    )

    order_item = models.ForeignKey(
        'students.OrderItem',
        on_delete=models.CASCADE,
        related_name='refund_disputes',
        null=True,
        blank=True
    )

    last_status_change = models.DateTimeField(auto_now_add=True)
    auto_escalate_at = models.DateTimeField(null=True, blank=True)
    auto_approve_at = models.DateTimeField(null=True, blank=True)

    # Additional fields
    rejection_reason = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    resolution_notes = models.TextField(
        blank=True,
        null=True,
        help_text=_('Final resolution explanation')
    )

    # Evidence/attachments
    client_evidence = models.JSONField(
        blank=True,
        null=True,
        help_text=_('Client submitted evidence (file URLs, screenshots, etc.)')
    )
    vendor_response = models.TextField(
        blank=True,
        null=True,
        help_text=_('Vendor response to the dispute')
    )
    vendor_evidence = models.JSONField(
        blank=True,
        null=True,
        help_text=_('Vendor submitted evidence (file URLs, screenshots, etc.)')
    )

    # Priority and urgency
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
            ('urgent', _('Urgent'))
        ],
        default='medium'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    # Additional tracking
    is_active = models.BooleanField(default=True)
    requires_investigation = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Refund & Dispute'
        verbose_name_plural = 'Refunds & Disputes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['deal', 'status']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['vendor', 'status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def update_stage(self, new_stage):
        self.current_stage = new_stage
        self.stage_start_time = timezone.now()
        self.set_next_escalation_time()
        self.save()

    def set_next_escalation_time(self):
        if self.current_stage == 'student_coach':
            self.next_escalation_time = self.stage_start_time + timedelta(days=7)
        elif self.current_stage == 'receptionist':
            self.next_escalation_time = self.stage_start_time + timedelta(days=7)
        else:
            self.next_escalation_time = None
        self.save()

    def check_for_escalation(self):
        if self.next_escalation_time and timezone.now() > self.next_escalation_time:
            if self.current_stage == 'student_coach':
                self.update_stage('receptionist')
                # Notify receptionist
            elif self.current_stage == 'receptionist':
                self.update_stage('director')
                # Notify director
            return True
        return False

    def add_message(self, sender, message, attachments=None):
        msg = RefundDisputeMessage.objects.create(
            dispute=self,
            sender=sender,
            message=message,
            attachments=attachments or []
        )
        self.last_message_time = timezone.now()
        self.save()
        return msg

    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)

            # Ensure unique slug
            original_slug = self.slug
            counter = 1
            while RefundDispute.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        # Set client from deal if not already set
        if self.deal and not self.client_id:
            self.client = self.deal.user

        # Set vendor from deal if not already set
        if self.deal and not self.vendor_id:
            first_item = self.deal.items.first()
            if first_item:
                if hasattr(first_item, 'product') and first_item.product:
                    self.vendor = first_item.product.creator
                elif hasattr(first_item, 'service') and first_item.service:
                    self.vendor = first_item.service.creator

        # Auto-populate original amount from deal if not provided
        if not self.original_amount and self.deal:
            self.original_amount = self.deal.total_price

        # Auto-calculate refund amounts if percentages are provided
        if (self.approved_refund_amount and
                self.vendor_percentage is not None and
                self.client_percentage is not None):
            self.vendor_refund_amount = (self.approved_refund_amount * self.vendor_percentage) / 100
            self.client_refund_amount = (self.approved_refund_amount * self.client_percentage) / 100

        # Set timestamps based on status changes
        if self.pk:  # If updating existing record
            try:
                original = RefundDispute.objects.get(pk=self.pk)
                if original.status != self.status:
                    from django.utils import timezone
                    if self.status == RefundStatus.APPROVED:
                        self.approved_at = timezone.now()
                    elif self.status == RefundStatus.REJECTED:
                        self.rejected_at = timezone.now()
                    elif self.status == RefundStatus.RESOLVED:
                        self.resolved_at = timezone.now()
            except RefundDispute.DoesNotExist:
                pass  # New object, ignore

        from django.utils import timezone
        from datetime import timedelta

        # Set auto-escalate and auto-approve timestamps when status changes to PENDING
        if self.status == RefundStatus.PENDING and not self.pk:
            now = timezone.now()
            self.last_status_change = now
            self.auto_escalate_at = now + timedelta(days=3)
            self.auto_approve_at = now + timedelta(days=7)

        # Check for automatic status changes
        if self.pk and self.status == RefundStatus.PENDING:
            now = timezone.now()
            if self.auto_escalate_at and now >= self.auto_escalate_at:
                self.status = RefundStatus.ESCALATED
                self.is_escalated = True
                self.last_status_change = now
            elif self.auto_approve_at and now >= self.auto_approve_at:
                self.status = RefundStatus.APPROVED
                self.approved_refund_amount = self.requested_refund_amount
                self.client_percentage = 100
                self.vendor_percentage = 0
                self.last_status_change = now
                self.approved_at = now

        super().save(*args, **kwargs)

    def clean(self):
        """Validate model data"""
        from django.core.exceptions import ValidationError
        errors = {}

        # Validate percentages sum to 100 if both are provided
        if (self.vendor_percentage is not None and
                self.client_percentage is not None):
            if abs((self.vendor_percentage + self.client_percentage) - 100) > 0.01:  # Allow for floating point precision
                errors['vendor_percentage'] = _('Vendor and client percentages must sum to 100%')
                errors['client_percentage'] = _('Vendor and client percentages must sum to 100%')

        # Validate requested refund amount doesn't exceed original amount
        if self.requested_refund_amount and self.original_amount:
            if self.requested_refund_amount > self.original_amount:
                errors['requested_refund_amount'] = _('Requested refund cannot exceed original amount')

        # Validate approved refund amount doesn't exceed requested amount
        if self.approved_refund_amount and self.requested_refund_amount:
            if self.approved_refund_amount > self.requested_refund_amount:
                errors['approved_refund_amount'] = _('Approved refund cannot exceed requested amount')

        # Skip client/deal validation in clean() - handle it in the form instead
        # This avoids RelatedObjectDoesNotExist errors during form validation

        if errors:
            raise ValidationError(errors)

    def get_refund_percentage(self):
        """Calculate what percentage of original amount is being refunded"""
        if self.approved_refund_amount and self.original_amount:
            return (self.approved_refund_amount / self.original_amount) * 100
        return 0

    def is_full_refund(self):
        """Check if this is a full refund"""
        return self.refund_type == RefundType.FULL or self.get_refund_percentage() >= 95

    def can_be_approved(self):
        """Check if dispute can be approved"""
        return self.status in [RefundStatus.PENDING, RefundStatus.INVESTIGATING]

    def can_be_rejected(self):
        """Check if dispute can be rejected"""
        return self.status in [RefundStatus.PENDING, RefundStatus.INVESTIGATING]

    def can_be_resolved(self):
        """Check if dispute can be marked as resolved"""
        return self.status == RefundStatus.APPROVED

    @property
    def days_since_created(self):
        """Get number of days since dispute was created"""
        return (timezone.now() - self.created_at).days

    @property
    def is_overdue(self):
        """Check if dispute is overdue (more than 7 days old and still pending)"""
        return self.status in [RefundStatus.PENDING, RefundStatus.INVESTIGATING] and self.days_since_created > 7


class RefundDisputeAttachment(models.Model):
    """
    Model for storing file attachments related to refund disputes
    """
    refund_dispute = models.ForeignKey(
        RefundDispute,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='refund_disputes/attachments/',
        help_text=_('Evidence files, screenshots, documents, etc.')
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_dispute_attachments'
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Description of the attachment')
    )
    file_type = models.CharField(
        max_length=20,
        choices=[
            ('image', _('Image')),
            ('document', _('Document')),
            ('video', _('Video')),
            ('other', _('Other'))
        ],
        default='other'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Refund Dispute Attachment'
        verbose_name_plural = 'Refund Dispute Attachments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Attachment for {self.refund_dispute.title}"





class CustomRole(models.Model):
    # Permission choices will map to view names in club_dashboard
    PERMISSION_CHOICES_EN = [
        ('club_dashboard_index', 'View Dashboard'),
        ('viewStudents', 'View Customers'),
        ('addStudent', 'Add Customers'),
        ('editStudent', 'Edit Customers'),
        ('deleteStudent', 'Delete Customers'),
        ('viewCoachs', 'View Vendors'),
        ('addCoach', 'Add Vendors'),
        ('editCoach', 'Edit Vendors'),
        ('deleteCoach', 'Delete Vendors'),
        ('viewArticles', 'View Articles'),
        ('addArticle', 'Add Articles'),
        ('editArticle', 'Edit Articles'),
        ('deleteArticle', 'Delete Articles'),
        ('viewDirectors', 'View Staff'),
        ('addDirector', 'Add Staff'),
        ('editDirector', 'Edit Staff'),
        ('deleteDirector', 'Delete Staff'),
        ('viewClubNotifications', 'View Notifications'),
        ('club_orders', 'View Orders'),
        ('update_order_status', 'Manage Orders'),
        ('club_financial_dashboard', 'View Revenue'),
        ('manage_products', 'Manage Product Approval'),
        ('manage_services', 'Manage Service Approval'),
        ('commission_list', 'View Commissions'),
        ('refund_dashboard', 'Manage Conflicts'),
        ('delete_review', 'Delete Customer Reviews'),
        ('category_list', 'View Categories'),
        ('reviews_list', 'View Customer Reviews')
    ]

    PERMISSION_CHOICES_AR = [
        ('club_dashboard_index', 'عرض لوحة التحكم'),
        ('viewStudents', 'عرض العملاء'),
        ('addStudent', 'إضافة العملاء'),
        ('editStudent', 'تعديل العملاء'),
        ('deleteStudent', 'حذف العملاء'),
        ('viewCoachs', 'عرض التجار'),
        ('addCoach', 'إضافة التجار'),
        ('editCoach', 'تعديل التجار'),
        ('deleteCoach', 'حذف التجار'),
        ('viewArticles', 'عرض المقالات'),
        ('addArticle', 'إضافة المقالات'),
        ('editArticle', 'تعديل المقالات'),
        ('deleteArticle', 'حذف المقالات'),
        ('viewDirectors', 'عرض الموظفين'),
        ('addDirector', 'إضافة الموظفين'),
        ('editDirector', 'تعديل الموظفين'),
        ('deleteDirector', 'حذف الموظفين'),
        ('viewClubNotifications', 'عرض الإشعارات'),
        ('club_orders', 'عرض الطلبات'),
        ('update_order_status', 'التحكم بالطلبات'),
        ('club_financial_dashboard', 'عرض الإيرادات'),
        ('manage_products', 'التحكم في قبول المنتجات'),
        ('manage_services', 'التحكم في قبول الخدمات'),
        ('commission_list', 'عرض العمولات'),
        ('refund_dashboard', 'التحكم في النزاعات'),
        ('delete_review', 'حذف اراء العملاء'),
        ('category_list', 'عرض الفئات'),
        ('reviews_list', 'عرض اراء العملاء')
    ]

    name_en = models.CharField(max_length=100, verbose_name='Role Name (English)')
    name_ar = models.CharField(max_length=100, verbose_name='Role Name (Arabic)')
    permissions = models.JSONField(default=list)  # Will store list of permission codes
    club = models.ForeignKey('accounts.ClubsModel', on_delete=models.CASCADE, related_name="custom_roles")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name_en} / {self.name_ar} ({self.club.name})"

    def get_name(self, language_code='en'):
        """Get role name based on language"""
        if language_code == 'ar':
            return self.name_ar
        return self.name_en

    def get_permissions_display(self, language_code='en'):
        """Returns human-readable permission names based on language"""
        if language_code == 'ar':
            permission_dict = dict(self.PERMISSION_CHOICES_AR)
        else:
            permission_dict = dict(self.PERMISSION_CHOICES_EN)
        return [permission_dict.get(code, code) for code in self.permissions]

    def has_permission(self, permission_code):
        """Check if role has specific permission"""
        return permission_code in self.permissions

    @classmethod
    def get_permission_choices(cls, language_code='en'):
        """Get permission choices based on language"""
        if language_code == 'ar':
            return cls.PERMISSION_CHOICES_AR
        else:
            return cls.PERMISSION_CHOICES_EN


from django.db import models
from django.core.validators import FileExtensionValidator


class LandingPageContent(models.Model):
    # Hero Section
    hero_title_en = models.CharField(max_length=200, default="The Premier Platform for")
    hero_title_ar = models.CharField(max_length=200, default="المنصة الرائدة")
    hero_subtitle_en = models.CharField(max_length=200, default="Vendor Excellence")
    hero_subtitle_ar = models.CharField(max_length=200, default="للتميز في التجارة")
    hero_description_en = models.TextField(
        default="Discover and connect with thousands of vendors to find the perfect products for your needs.")
    hero_description_ar = models.TextField(default="اكتشف وتواصل مع آلاف التجار لتجد المنتجات المثالية لاحتياجاتك.")
    hero_image = models.ImageField(upload_to='landing/hero/', blank=True, null=True)

    # About Section
    about_title_en = models.CharField(max_length=200, default="Why Choose Our Platform")
    about_title_ar = models.CharField(max_length=200, default="لماذا تختار منصتنا")
    about_description_en = models.TextField(
        default="We provide the tools and connections you need to succeed in your business journey.")
    about_description_ar = models.TextField(default="نحن نقدم الأدوات والروابط التي تحتاجها للنجاح في رحلتك التجارية.")

    # Features Section
    features_title_en = models.CharField(max_length=200, default="Platform Features")
    features_title_ar = models.CharField(max_length=200, default="ميزات المنصة")

    # CTA Section
    cta_title_en = models.CharField(max_length=200, default="Start organizing your business today")
    cta_title_ar = models.CharField(max_length=200, default="ابدأ في تنظيم عملك اليوم")
    cta_description_en = models.TextField(
        default="Join thousands of vendors using our platform to improve their performance and management")
    cta_description_ar = models.TextField(
        default="انضم إلى الآلاف من التجار الذين يستخدمون منصتنا لتحسين أدائهم وإدارتهم")

    # Meta
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Landing Page Content"
        verbose_name_plural = "Landing Page Contents"

    def __str__(self):
        return f"Landing Content - {self.club.name}"


class LandingPageFeature(models.Model):
    landing_content = models.ForeignKey(LandingPageContent, on_delete=models.CASCADE, related_name='features')
    icon = models.CharField(max_length=100, help_text="Font Awesome icon class (e.g., fa-shopping-cart)")
    title_en = models.CharField(max_length=200)
    title_ar = models.CharField(max_length=200)
    description_en = models.TextField()
    description_ar = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title_en


class LandingPageBanner(models.Model):
    landing_content = models.ForeignKey(LandingPageContent, on_delete=models.CASCADE, related_name='banners')
    title_en = models.CharField(max_length=200)
    title_ar = models.CharField(max_length=200)
    image = models.ImageField(upload_to='landing/banners/',
                              validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])])
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title_en


class LandingPageFAQ(models.Model):
    landing_content = models.ForeignKey(LandingPageContent, on_delete=models.CASCADE, related_name='faqs')
    question_en = models.CharField(max_length=300)
    question_ar = models.CharField(max_length=300)
    answer_en = models.TextField()
    answer_ar = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question_en


class NavItem(models.Model):
    landing_content = models.ForeignKey(LandingPageContent, on_delete=models.CASCADE, related_name='nav_items')
    name_en = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    href = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name_en


from django.db import models
from accounts.models import ClubsModel


class ClubContact(models.Model):
    """Contact information for the club"""
    club = models.OneToOneField(ClubsModel, on_delete=models.CASCADE, related_name='contact_info')

    # Contact Details
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address_en = models.TextField(blank=True, null=True)
    address_ar = models.TextField(blank=True, null=True)
    working_hours_en = models.TextField(blank=True, null=True)
    working_hours_ar = models.TextField(blank=True, null=True)

    # Social Media Links
    facebook = models.URLField(max_length=200, blank=True, null=True)
    twitter = models.URLField(max_length=200, blank=True, null=True)
    instagram = models.URLField(max_length=200, blank=True, null=True)
    linkedin = models.URLField(max_length=200, blank=True, null=True)
    youtube = models.URLField(max_length=200, blank=True, null=True)
    whatsapp = models.URLField(max_length=200, blank=True,
                               null=True)  # Changed from CharField to URLField with 200 max_length

    # Footer
    footer_text_en = models.TextField(blank=True, null=True)
    footer_text_ar = models.TextField(blank=True, null=True)
    footer_logo = models.ImageField(upload_to='contact/footer_logos/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Club Contact Information"
        verbose_name_plural = "Club Contact Information"

    def __str__(self):
        return f"Contact Info for {self.club.name}"

    @property
    def address(self):
        """Return address based on current language"""
        from django.utils import translation
        lang = translation.get_language()
        if lang == 'ar' and self.address_ar:
            return self.address_ar
        return self.address_en or self.address_ar or ''

    @property
    def working_hours(self):
        """Return working hours based on current language"""
        from django.utils import translation
        lang = translation.get_language()
        if lang == 'ar' and self.working_hours_ar:
            return self.working_hours_ar
        return self.working_hours_en or self.working_hours_ar or ''

    @property
    def footer_text(self):
        """Return footer text based on current language"""
        from django.utils import translation
        lang = translation.get_language()
        if lang == 'ar' and self.footer_text_ar:
            return self.footer_text_ar
        return self.footer_text_en or self.footer_text_ar or ''

    def get_social_links(self):
        """Return list of active social media links with their icons"""
        social_media = []

        if self.facebook:
            social_media.append(('Facebook', 'fab fa-facebook-f', self.facebook, 'فيسبوك', 'Facebook'))
        if self.twitter:
            social_media.append(('Twitter', 'fab fa-twitter', self.twitter, 'تويتر', 'Twitter'))
        if self.instagram:
            social_media.append(('Instagram', 'fab fa-instagram', self.instagram, 'إنستغرام', 'Instagram'))
        if self.linkedin:
            social_media.append(('LinkedIn', 'fab fa-linkedin-in', self.linkedin, 'لينكد إن', 'LinkedIn'))
        if self.youtube:
            social_media.append(('YouTube', 'fab fa-youtube', self.youtube, 'يوتيوب', 'YouTube'))

        return social_media


from django.db import models
from accounts.models import ClubsModel
from django.core.validators import MinValueValidator, MaxValueValidator


class VATSettings(models.Model):
    """
    VAT (Value Added Tax) settings for each club.
    Allows club directors to enable/disable VAT and set the percentage.
    """
    club = models.OneToOneField(
        ClubsModel,
        on_delete=models.CASCADE,
        related_name='vat_settings',
        verbose_name='Club'
    )
    is_enabled = models.BooleanField(
        default=False,
        verbose_name='Enable VAT',
        help_text='Enable or disable VAT for this club'
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
        verbose_name='VAT Percentage',
        help_text='VAT percentage to be applied (0-100)'
    )
    currency = models.CharField(
        max_length=10,
        default='SAR',
        verbose_name='Currency',
        help_text='Currency code (e.g., SAR, USD, EUR)'
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'VAT Settings'
        verbose_name_plural = 'VAT Settings'

    def __str__(self):
        status = 'Enabled' if self.is_enabled else 'Disabled'
        return f"{self.club.name} - VAT {status} ({self.percentage}%)"

    def calculate_vat(self, amount):
        """Calculate VAT amount for a given price. Returns 0 if VAT is disabled."""
        if not self.is_enabled:
            return 0
        return (amount * self.percentage) / 100

    def calculate_total_with_vat(self, amount):
        """Calculate total amount including VAT. Returns original amount if VAT is disabled."""
        if not self.is_enabled:
            return amount
        vat_amount = self.calculate_vat(amount)
        return amount + vat_amount
