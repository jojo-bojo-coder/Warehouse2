from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import accounts.models


class Notification(models.Model):
    club = models.ForeignKey(
        'accounts.CoachProfile',  # ✅ Correct reference to ClubsModel from accounts
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="التاجر"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # ✅ Prevents issues when a user is deleted
        null=True,
        blank=True,
        related_name="notification",
        verbose_name="المستخدم"
    )
    NOTIFICATION_TYPES = [
        ('order', 'New Order'),
        ('refund', 'Refund Request'),
        ('review', 'New Review'),
        ('ticket', 'Support Ticket'),
        ('other', 'Other'),
    ]
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='other',
        verbose_name="نوع الإشعار"
    )
    message = models.TextField(verbose_name="الرسالة")
    is_read = models.BooleanField(default=False, verbose_name="تم القراءة")
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_content_type = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")  # ✅ Added for tracking notification updates

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.message[:50]}..."


from accounts.models import CoachProfile,ReceptionistProfile,UserProfile
class CoachReceptionistTicket(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name='sent_tickets')
    receptionist = models.ForeignKey(ReceptionistProfile, on_delete=models.CASCADE, related_name='received_tickets', null=True, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)
    assignment_time = models.DateTimeField(null=True, blank=True)
    resolution_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"

    def assign_to_receptionist(self, receptionist):
        self.receptionist = receptionist
        self.status = 'active'
        self.assignment_time = timezone.now()
        self.save()
        receptionist.set_status('busy')
        receptionist.last_assignment_time = timezone.now()
        receptionist.save()

    def mark_resolved(self, hold_minutes=15):
        if self.receptionist:
            self.receptionist.set_status('hold', hold_minutes)
        self.status = 'resolved'
        self.resolution_time = timezone.now()
        self.save()

class TicketMessage(models.Model):
    ticket = models.ForeignKey(CoachReceptionistTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message #{self.id} for Ticket {self.ticket.id}"


from django.db import models
from students.models import ProductsModel, ServicesModel
from accounts.models import CoachProfile, ClubsModel
from django.utils import timezone

class PromotionFeature(models.Model):
    """Individual features that can be added to promotions"""
    club = models.ForeignKey(ClubsModel, on_delete=models.CASCADE, related_name='promotion_features')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0,
                                         help_text="Multiplier for base price (e.g., 1.5 = 50% increase)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('club', 'name')

    def __str__(self):
        return self.name

class Promotion(models.Model):
    PROMOTION_TYPES = [
        ('product', 'منتج'),
        ('service', 'خدمة'),
    ]

    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('pending', 'في انتظار الموافقة'),
        ('rejected', 'مرفوض'),
        ('expired', 'منتهي الصلاحية'),
    ]

    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name='promotions')
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPES)
    product = models.ForeignKey(ProductsModel, on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey(ServicesModel, on_delete=models.CASCADE, null=True, blank=True)
    features = models.ManyToManyField(PromotionFeature, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    duration_days = models.PositiveIntegerField(default=1)
    base_price_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Calculate total price when saving"""
        # Only calculate price if this is a new object or specific fields are being updated
        if not self.pk or 'duration_days' in kwargs.get('update_fields', []):
            # Only calculate if we have features (for existing objects with M2M relations)
            if self.pk:
                self.calculate_price()
        super().save(*args, **kwargs)

    def calculate_price(self):
        """Calculate total price based on duration and features"""
        multiplier = 1.0
        if self.pk:  # Only if the object exists in database
            for feature in self.features.all():
                multiplier *= feature.price_multiplier
        self.total_price = self.base_price_per_day * self.duration_days * multiplier

    def get_promotion_item_name(self):
        if self.promotion_type == 'product' and self.product:
            return self.product.title
        elif self.promotion_type == 'service' and self.service:
            return self.service.title
        return "Unknown Item"

    def is_active(self):
        if self.status != 'active':
            return False
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def get_remaining_days(self):
        if not self.end_date or not self.is_active():
            return 0
        return (self.end_date - timezone.now()).days


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from accounts.models import CoachProfile, StudentProfile


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
    ]

    coach = models.ForeignKey('accounts.CoachProfile', on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=5, decimal_places=2)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Student selection
    all_students = models.BooleanField(default=False)
    selected_students = models.ManyToManyField(StudentProfile, blank=True)

    # Product/service selection
    apply_to_all_products = models.BooleanField(default=False)
    apply_to_all_services = models.BooleanField(default=False)
    products = models.ManyToManyField('students.ProductsModel', blank=True)
    services = models.ManyToManyField('students.ServicesModel', blank=True)

    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_uses = models.PositiveIntegerField(default=1)
    times_used = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"

    def __str__(self):
        return f"{self.code} - {self.get_discount_type_display()}"

    def is_valid(self, student=None, cart_items=None):
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.start_date or now > self.end_date:
            return False
        if self.times_used >= self.max_uses:
            return False
        if student and not self.all_students and not self.selected_students.filter(id=student.id).exists():
            return False
        if cart_items:
            if not self._is_valid_for_cart_items(cart_items):
                return False
        return True

    def _is_valid_for_cart_items(self, cart_items):
        if self.apply_to_all_products and self.apply_to_all_services:
            return True

        valid = False
        for item in cart_items:
            if hasattr(item, 'product') and item.product:
                if self.apply_to_all_products or self.products.filter(id=item.product.id).exists():
                    valid = True
            elif hasattr(item, 'service') and item.service:
                if self.apply_to_all_services or self.services.filter(id=item.service.id).exists():
                    valid = True
        return valid

    def calculate_discount(self, amount):
        if self.discount_type == 'percentage':
            discount = (amount * self.discount_value) / Decimal('100')
            if self.max_discount and discount > self.max_discount:
                return self.max_discount
            return discount
        else:
            return min(self.discount_value, amount)

    def activate_for_student(self, student):
        activation, created = CouponActivation.objects.get_or_create(
            coupon=self,
            student=student
        )
        if not activation.is_active:
            activation.is_active = True
            activation.activated_at = timezone.now()
            activation.save()
            return True
        return False

    def is_valid(self, student=None, cart_items=None):
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.start_date or now > self.end_date:
            return False
        if self.times_used >= self.max_uses:
            return False
        if student:
            # Check if student is eligible and has activated the coupon
            if not self.all_students and not self.selected_students.filter(id=student.id).exists():
                return False
            try:
                activation = self.activations.get(student=student)
                if not activation.is_active:
                    return False
            except CouponActivation.DoesNotExist:
                return False
        if cart_items:
            if not self._is_valid_for_cart_items(cart_items):
                return False
        return True


class CouponUsage(models.Model):
    coupon = models.ForeignKey('Coupon', on_delete=models.CASCADE, related_name='usages')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE)
    order = models.ForeignKey('students.Order', on_delete=models.SET_NULL, null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('coupon', 'order')
        verbose_name = "Coupon Usage"
        verbose_name_plural = "Coupon Usages"

    def __str__(self):
        return f"{self.coupon.code} used by {self.student.full_name}"

# Add to models.py after CouponUsage
class CouponActivation(models.Model):
    coupon = models.ForeignKey('Coupon', on_delete=models.CASCADE, related_name='activations')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('coupon', 'student')
        verbose_name = "Coupon Activation"
        verbose_name_plural = "Coupon Activations"

    def __str__(self):
        return f"{self.coupon.code} activation for {self.student.full_name}"


from django.db import models
from accounts.models import CoachProfile
from django.utils import timezone


class VendorWorkingHours(models.Model):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name='vendor_working_hours'
    )
    title = models.CharField(max_length=100, verbose_name="Schedule Title")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")

    # Days of week with working hours
    monday_open = models.TimeField(null=True, blank=True, verbose_name="Monday Open")
    monday_close = models.TimeField(null=True, blank=True, verbose_name="Monday Close")
    tuesday_open = models.TimeField(null=True, blank=True, verbose_name="Tuesday Open")
    tuesday_close = models.TimeField(null=True, blank=True, verbose_name="Tuesday Close")
    wednesday_open = models.TimeField(null=True, blank=True, verbose_name="Wednesday Open")
    wednesday_close = models.TimeField(null=True, blank=True, verbose_name="Wednesday Close")
    thursday_open = models.TimeField(null=True, blank=True, verbose_name="Thursday Open")
    thursday_close = models.TimeField(null=True, blank=True, verbose_name="Thursday Close")
    friday_open = models.TimeField(null=True, blank=True, verbose_name="Friday Open")
    friday_close = models.TimeField(null=True, blank=True, verbose_name="Friday Close")
    saturday_open = models.TimeField(null=True, blank=True, verbose_name="Saturday Open")
    saturday_close = models.TimeField(null=True, blank=True, verbose_name="Saturday Close")
    sunday_open = models.TimeField(null=True, blank=True, verbose_name="Sunday Open")
    sunday_close = models.TimeField(null=True, blank=True, verbose_name="Sunday Close")

    is_active = models.BooleanField(default=True, verbose_name="Active Schedule")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-start_date']
        verbose_name = "Vendor Working Hours"
        verbose_name_plural = "Vendor Working Hours"

    def __str__(self):
        return f"{self.title} ({self.start_date} to {self.end_date})"

    def is_current(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.is_active

    def get_days_info(self):
        days = [
            {'name': 'Monday', 'field': 'monday'},
            {'name': 'Tuesday', 'field': 'tuesday'},
            {'name': 'Wednesday', 'field': 'wednesday'},
            {'name': 'Thursday', 'field': 'thursday'},
            {'name': 'Friday', 'field': 'friday'},
            {'name': 'Saturday', 'field': 'saturday'},
            {'name': 'Sunday', 'field': 'sunday'},
        ]

        for day in days:
            open_time = getattr(self, f'{day["field"]}_open')
            close_time = getattr(self, f'{day["field"]}_close')

            day['open'] = open_time
            day['close'] = close_time
            day['day'] = day['name']

            # Add Arabic day names if needed
            if hasattr(self, 'LANGUAGE_CODE') and self.LANGUAGE_CODE == 'ar':
                arabic_days = {
                    'Monday': 'الاثنين',
                    'Tuesday': 'الثلاثاء',
                    'Wednesday': 'الأربعاء',
                    'Thursday': 'الخميس',
                    'Friday': 'الجمعة',
                    'Saturday': 'السبت',
                    'Sunday': 'الأحد'
                }
                day['day'] = arabic_days[day['name']]

        return days