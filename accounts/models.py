from django.db import models
from django.contrib.auth.models import User
from .fields import citys
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.postgres.fields import JSONField
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


AccountTypeChoices = (
    ('1', 'admin'),
    ('2', 'director'),
    ('3', 'student'),
    ('4', 'coach'),
    ('5', 'receptionist'),
    ('6','administrator'),
    ('7', 'accountant'),
    ('8', 'vendor_manager'),
    ('9' , 'custom_profile')
)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image_base64 = models.TextField(blank=True, null=True)
    account_type = models.CharField(max_length=250, choices=AccountTypeChoices)
    creation_date = models.DateTimeField(auto_now_add=True)
    
    # ✅ Allow multiple directors per club
    director_profile = models.ForeignKey('DirectorProfile', on_delete=models.SET_NULL, null=True, blank=True)
    student_profile = models.ForeignKey('StudentProfile', on_delete=models.SET_NULL, null=True, blank=True)
    Coach_profile = models.ForeignKey('CoachProfile', on_delete=models.SET_NULL, null=True, blank=True)
    receptionist_profile = models.ForeignKey('ReceptionistProfile', on_delete=models.SET_NULL, null=True, blank=True)
    administrator_profile = models.ForeignKey('AdministrativeProfile', on_delete=models.SET_NULL, null=True, blank=True)
    accountant_profile = models.ForeignKey('AccountantProfile', on_delete=models.SET_NULL, null=True, blank=True)
    custom_role = models.ForeignKey('club_dashboard.CustomRole', on_delete=models.SET_NULL, null=True, blank=True)
    custom_role_profile = models.ForeignKey('CustomRoleProfile', on_delete=models.SET_NULL, null=True, blank=True)
    vendor_manager_profile = models.ForeignKey('VendorManagerProfile', on_delete=models.SET_NULL, null=True, blank=True)

    is_active = models.BooleanField(default=False)
    last_active_datetime = models.DateTimeField(null=True, blank=True)
    is_in_chat = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.get_account_type_display()}"


class ClubsModel(models.Model):
    name = models.CharField(max_length=250, unique=True, verbose_name="اسم الأكاديمية")
    club_profile_image_base64 = models.TextField(blank=True, null=True)
    desc = models.CharField(max_length=255, null=True, verbose_name="وصف قصير")
    about = models.TextField(max_length=255, null=True, verbose_name="نبذة")
    city = models.CharField(max_length=255, choices=citys, null=True, verbose_name="المدينة")
    district = models.CharField(max_length=250, null=True, verbose_name="الحي")
    street = models.CharField(max_length=250, null=True, verbose_name="الشارع")
    creation_date = models.DateTimeField(auto_now_add=True)
    chat_enabled = models.BooleanField(default=True, verbose_name="دردشة مفعلة")
    pricing = models.JSONField(default=list, blank=True)
    productsDescription = models.TextField(null=True, blank=True, verbose_name="وصف المنتجات")
    articlesDescription = models.TextField(null=True, blank=True, verbose_name="وصف المقالات")
    bank_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="اسم البنك")
    account_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="اسم الحساب")
    account_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="رقم الحساب")
    iban = models.CharField(max_length=50, null=True, blank=True, verbose_name="رقم الآيبان")
    swift_code = models.CharField(max_length=50, null=True, blank=True, verbose_name="كود السويفت")
    bank_country = models.CharField(max_length=100, null=True, blank=True, verbose_name="بلد البنك")
    bank_address = models.TextField(null=True, blank=True, verbose_name="عنوان البنك")
    # Subscription Plan
    current_plan_id = models.IntegerField(default=1)  # Default to free plan
    promotion_base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100.00,
        help_text="Base price per day for promotions"
    )

    def __str__(self):
        return str(self.name)

    def get_max_players(self):
        try:
            # Ensure pricing is a list
            if not isinstance(self.pricing, list):
                return 20  # Default if pricing is not a list

            # Adjust for 0-based indexing if needed
            # If current_plan_id is 1-based (1,2,3,...) but list is 0-based
            list_index = self.current_plan_id - 1 if self.current_plan_id > 0 else 0

            # Check if index is valid
            if list_index >= len(self.pricing):
                return 20  # Default if index out of range

            current_plan = self.pricing[list_index]

            # Check if current_plan is a dictionary
            if not isinstance(current_plan, dict):
                return 20  # Default if not a dictionary

            # Look for features
            features = current_plan.get('features', [])

            for feature in features:
                if isinstance(feature, str):
                    if 'لاعب' in feature:
                        # Extract the number from the feature string
                        numbers = [int(s) for s in feature.split() if s.isdigit()]
                        if numbers:
                            return numbers[0]
                        elif 'غير محدود' in feature or 'unlimited' in feature.lower():
                            return float('inf')  # Unlimited

            return 20  # Default if not found

        except (IndexError, KeyError, AttributeError, TypeError, ValueError) as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in get_max_players for club {self.id}: {str(e)}")
            return 20  # Default if error occurs

    @property
    def can_add_more_players(self):
        max_players = self.get_max_players()
        if max_players == float('inf'):
            return True
        current_players = StudentProfile.objects.filter(club=self).count()
        return current_players < max_players

    @property
    def players_remaining(self):
        max_players = self.get_max_players()
        if max_players == float('inf'):
            return "غير محدود"
        current_players = StudentProfile.objects.filter(club=self).count()
        return max(0, max_players - current_players)




class CustomRoleProfile(models.Model):
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    about = models.TextField(null=True, blank=True)
    profile_image_base64 = models.TextField(blank=True, null=True)
    club = models.ForeignKey('ClubsModel', on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.club.name}"

    class Meta:
        verbose_name = "Custom Role Profile"
        verbose_name_plural = "Custom Role Profiles"




from .fields import REGIONS_AND_CITIES
class VendorManagerProfile(models.Model):
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    about = models.TextField(null=True, blank=True)
    region = models.CharField(
        max_length=50,
        choices=[(r, r) for r in REGIONS_AND_CITIES.keys()],
        verbose_name="المنطقة المسؤولة"
    )
    club = models.ForeignKey('ClubsModel', on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.region}"

    class Meta:
        verbose_name = "مدير التجار"
        verbose_name_plural = "مديري التجار"


class DirectorProfile(models.Model):
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    about = models.TextField(null=True, blank=True)
    
    # ✅ Ensure multiple directors per club
    club = models.ForeignKey('ClubsModel', on_delete=models.CASCADE, related_name="directors")

    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.club.name}"

SUBSCRIPTION_STATUS_CHOICES = (
    ('trial', 'تجريبي'),
    ('active', 'نشط'),
    ('expiring_soon', 'سينتهي قريبًا'),
    ('expired', 'منتهي'),
)

from django.utils.translation import get_language
from django.core.exceptions import ValidationError
class StudentProfile(models.Model):
    GENDER_CHOICES_EN = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    GENDER_CHOICES_AR = [
        ('M', 'ذكر'),
        ('F', 'أنثى'),
    ]

    @classmethod
    def get_gender_choices(cls):
        language = get_language()
        if language == 'ar':
            return cls.GENDER_CHOICES_AR
        else:
            return cls.GENDER_CHOICES_EN
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    birthday = models.DateField()
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES_EN,  # Default choices
        verbose_name="Gender"
    )
    profile_image_base64 = models.TextField(blank=True, null=True)
    about = models.TextField(null=True)
    club = models.ForeignKey('ClubsModel', on_delete=models.SET_NULL, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update choices based on current language
        self._meta.get_field('gender').choices = self.get_gender_choices()

    def __str__(self):
        return str(self.full_name)

    def age(self):
        return (timezone.now().date() - self.birthday).days // 365

    def save(self, *args, **kwargs):
        if self.club and not self.pk:
            max_players = self.club.get_max_players()
            if max_players != float('inf'):  # If not unlimited
                current_players = StudentProfile.objects.filter(club=self.club).count()
                if current_players >= max_players:
                    raise ValidationError(
                        f"هذا النادي لديه الحد الأقصى من اللاعبين ({max_players}) حسب الباقة الحالية. يرجى ترقية الباقة لإضافة المزيد من اللاعبين."
                    )
        super(StudentProfile, self).save(*args, **kwargs)

    def has_available_coupons(self):
        from coach_dashboard.models import Coupon
        return Coupon.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).filter(
            models.Q(all_students=True) |
            models.Q(selected_students=self)
        ).exists()


from django.core.validators import RegexValidator
from django.shortcuts import redirect
from django.http import HttpRequest

class CoachProfile(models.Model):
    POLICY_CHOICES = [
        ('terms_conditions', 'سياسة الشروط والأحكام'),
        ('refund_policy', 'سياسة الاسترجاع'),
    ]

    APPROVAL_STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('approved', 'مقبول'),
        ('rejected', 'مرفوض'),
    ]


    BUSINESS_DOCUMENT_CHOICES = [
        ('', 'اختر نوع الوثيقة'),
        ('freelance', 'وثيقة العمل الحر'),
        ('commercial_register', 'صورة السجل التجاري'),
    ]

    REGION_CHOICES = [
        ('الرياض', 'الرياض'),
        ('مكة المكرمة', 'مكة المكرمة'),
        ('القصيم', 'القصيم'),
        ('المنطقة الشرقية', 'المنطقة الشرقية'),
        ('عسير', 'عسير'),
        ('تيرك', 'تيرك'),
        ('حائل', 'حائل'),
        ('الحدود الشمالية', 'الحدود الشمالية'),
        ('جازان', 'جازان'),
        ('نجران', 'نجران'),
        ('الباحة', 'الباحة'),
        ('الجوف', 'الجوف'),
        ('المدينة المنورة', 'المدينة المنورة'),
    ]

    full_name = models.CharField(
        max_length=100,
        verbose_name="الاسم الكامل",
        validators=[RegexValidator(
            regex=r'^[\u0600-\u06FFa-zA-Z\s]+$',
            message='الاسم الكامل يمكن أن يحتوي فقط على أحرف عربية وإنجليزية / Full name can only contain Arabic and English letters'
        )]
    )
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    email = models.EmailField(verbose_name="البريد الإلكتروني", default="example@example.com")

    activity_type = models.ForeignKey(
        'club_dashboard.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="نوع النشاط"
    )

    subcategories = models.ManyToManyField(
        'club_dashboard.SubCategory',
        blank=True,
        verbose_name="التخصصات الفرعية",
        help_text="التخصصات الفرعية التي يعمل بها البائع"
    )

    # Commercial Registration Number (10 digits)
    commercial_registration_number = models.CharField(
        max_length=10,
        verbose_name="رقم السجل التجاري",
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='رقم السجل التجاري يجب أن يكون 10 أرقام بالضبط'
            )
        ],
        blank=True,
        null=True
    )

    # Commercial Registration Certificate
    commercial_registration_certificate = models.TextField(
        blank=True,
        null=True,
        verbose_name="شهادة السجل التجاري",
        help_text="Base64 encoded file (PDF or Image)"
    )

    # Working hours fields
    working_hours = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="ساعات العمل"
    )
    is_working_hours_enabled = models.BooleanField(
        default=False,
        verbose_name="تفعيل ساعات العمل"
    )
    special_hours = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="ساعات العمل الخاصة"
    )

    # Tax Number (15 digits, optional)
    tax_number = models.CharField(
        max_length=15,
        verbose_name="الرقم الضريبي",
        validators=[
            RegexValidator(
                regex=r'^\d{15}$',
                message='الرقم الضريبي يجب أن يكون 15 رقم بالضبط'
            )
        ],
        blank=True,
        null=True,
        help_text="اختياري - 15 رقم"
    )

    # Tax Certificate
    tax_certificate = models.TextField(
        blank=True,
        null=True,
        verbose_name="شهادة الرقم الضريبي",
        help_text="Base64 encoded file (PDF or Image)"
    )

    # Store Logo
    store_logo_base64 = models.TextField(
        blank=True,
        null=True,
        verbose_name="شعار المتجر",
        help_text="Base64 encoded image file"
    )

    # Business inf
    business_name_en = models.CharField(max_length=200, verbose_name="Business Name (English)"
                                        )
    business_name_ar = models.CharField(max_length=200, verbose_name="اسم النشاط التجاري (عربي)"
                                        )
    description = models.TextField(
        verbose_name="وصف الخدمة",
        blank=True,
        default="",
        validators=[RegexValidator(
            regex=r'^[\u0600-\u06FFa-zA-Z0-9\s\.\,\!\?\-\_\(\)\:\;\'\"\@\#\$\%\&\*\+\=\[\]\{\}\\\/\<\>]+$',
            message='الوصف يمكن أن يحتوي فقط على أحرف عربية وإنجليزية وأرقام ورموز محددة / Description can only contain Arabic, English letters, numbers, and specific symbols'
        )]
    )

    business_photo_base64 = models.TextField(
        blank=True,
        null=True,
        verbose_name="صورة النشاط التجاري",
        help_text="Base64 encoded image file for the business"
    )

    business_phone_numbers = models.JSONField(
        default=list,
        blank=True,
        verbose_name="أرقام التواصل التجارية",
        help_text="List of business contact numbers in JSON format"
    )

    whatsapp_business_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="رقم الواتساب التجاري"
    )

    # Business document fields
    business_document_type = models.CharField(
        max_length=50,
        choices=BUSINESS_DOCUMENT_CHOICES,
        verbose_name="نوع وثيقة النشاط التجاري",
        blank=True,
        default=''
    )
    business_document_file = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملف الوثيقة التجارية",
        help_text="Base64 encoded file (PDF or Image)"
    )
    number_of_branches = models.PositiveIntegerField(
        verbose_name="Number of Branches",
        default=1,
        help_text="عدد الفروع"
    )

    branches = models.JSONField(
        default=list,
        blank=True,
        verbose_name="فروع النشاط التجاري",
        help_text="معلومات عن فروع النشاط التجاري"
    )

    # Location fields
    region = models.CharField(
        max_length=50,
        choices=REGION_CHOICES,
        verbose_name="المنطقة",
        default="غير محددة"
    )

    city = models.CharField(
        max_length=100,
        verbose_name="المدينة",
        validators=[RegexValidator(
            regex=r'^[\u0600-\u06FFa-zA-Z\s\-]+$',
            message='اسم المدينة يمكن أن يحتوي فقط على أحرف عربية وإنجليزية / City name can only contain Arabic and English letters'
        )]
    )
    district = models.CharField(
        max_length=100,
        verbose_name="الحي",
        validators=[RegexValidator(
            regex=r'^[\u0600-\u06FFa-zA-Z\s\-]+$',
            message='اسم الحي يمكن أن يحتوي فقط على أحرف عربية وإنجليزية / District name can only contain Arabic and English letters'
        )]
    )

    street = models.CharField(
        max_length=200,
        verbose_name="الشارع",
        validators=[RegexValidator(
            regex=r'^[\u0600-\u06FFa-zA-Z0-9\s\-\.\,]+$',
            message='اسم الشارع يمكن أن يحتوي فقط على أحرف عربية وإنجليزية وأرقام / Street name can only contain Arabic, English letters, and numbers'
        )]
    )

    # Profile image
    profile_image_base64 = models.TextField(blank=True, null=True, default="")


    vendor_classification = models.CharField(
        max_length=50,
        default='silver',
        verbose_name="تصنيف البائع"
    )

    # Approval system
    club = models.ForeignKey('ClubsModel', on_delete=models.CASCADE, verbose_name="النادي", default=1)
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
        verbose_name="حالة الموافقة"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_vendors'
    )
    # Notes from director
    approval_notes = models.TextField(blank=True, verbose_name="ملاحظات المدير", default="")
    policy_documents = models.JSONField(default=dict, blank=True)
    policies_approved = models.BooleanField(default=False)

    # Bank info
    bank_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="اسم البنك")
    account_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="اسم الحساب")
    account_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="رقم الحساب")
    iban = models.CharField(max_length=50, null=True, blank=True, verbose_name="رقم الآيبان")

    class Meta:
        verbose_name = "بائع"
        verbose_name_plural = "البائعين"

    def __str__(self):
        return f"{self.full_name} - {self.business_name_ar or self.business_name_en} - {self.activity_type.name if self.activity_type else 'No Activity'}"

    def clean(self):
        """Validate that the city belongs to the selected region"""
        from .fields import REGIONS_AND_CITIES  # Import your regions data

        super().clean()

        if self.region and self.city:
            valid_cities = REGIONS_AND_CITIES.get(self.region, [])
            if self.city not in valid_cities:
                raise ValidationError(
                    f"المدينة {self.city} غير موجودة في المنطقة {self.region}"
                )

        if self.number_of_branches > 1 and not self.branches:
            raise ValidationError(
                "يجب إضافة معلومات الفروع عندما يكون عدد الفروع أكثر من واحد"
            )

        if self.branches and len(self.branches) != self.number_of_branches:
            raise ValidationError(
                f"عدد الفروع المضافة ({len(self.branches)}) لا يتطابق مع العدد المحدد ({self.number_of_branches})"
            )

    def get_branches_display(self):
        """Get formatted branch information"""
        if not self.branches:
            return []

        return [
            {
                'number': i + 1,
                'city': branch.get('city', ''),
                'district': branch.get('district', ''),
                'street': branch.get('street', ''),
                'full_address': f"{branch.get('street', '')}, {branch.get('district', '')}, {branch.get('city', '')}"
            }
            for i, branch in enumerate(self.branches)
        ]

    def save(self, *args, **kwargs):
        if not self.pk and not self.vendor_classification:
            self.assign_optimal_classification()

        if self.vendor_classification:
            self.vendor_classification = self.vendor_classification.strip().lower()

        super().save(*args, **kwargs)

    def assign_optimal_classification(self):
        """Assign the classification with highest commission available"""
        from club_dashboard.models import Commission

        highest_commission = Commission.objects.filter(
            club=self.club,
            commission_type='vendor',
            is_active=True
        ).order_by('-commission_rate').first()

        if highest_commission:
            self.vendor_classification = highest_commission.vendor_classification
        else:
            self.vendor_classification = 'silver'  # Default fallback

    def get_current_commission_rate(self):
        """Get the current commission rate for this vendor after applying any discounts"""
        from club_dashboard.models import Commission

        # Get the vendor's base commission
        if hasattr(self, 'commission_assignment'):
            vendor_commission = self.commission_assignment.commission
        else:
            vendor_commission = Commission.objects.filter(
                club=self.club,
                commission_type='vendor',
                vendor_classification=self.vendor_classification,
                is_active=True
            ).first()

        if not vendor_commission:
            return 18.00  # Default fallback

        # Apply any active time period discounts
        return Commission.get_effective_rate(vendor_commission)

    def approve(self, approved_by_user, notes=""):
        """Approve the vendor"""
        self.approval_status = 'approved'
        self.approved_at = timezone.now()
        self.approved_by = approved_by_user
        self.approval_notes = notes
        self.save()

        # Assign commission to vendor
        self.assign_commission()

        # Create UserProfile when approved
        self.create_user_profile()

        # Send approval email with password
        subject = "Your Vendor Account Has Been Approved"
        context = {
            'vendor': self,
            'password': "1234",  # This should be the raw password used in create_user_profile()
            'login_url': settings.LOGIN_URL,
        }
        html_message = render_to_string('accounts/emails/vendor_approved.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            fail_silently=False,
        )

        return True

    def assign_commission(self):
        """Assign commission to approved vendor"""
        from club_dashboard.models import Commission, VendorCommissionAssignment

        # Get the appropriate commission
        commission = Commission.get_vendor_commission(self.club, self)

        # Create or update commission assignment
        assignment, created = VendorCommissionAssignment.objects.get_or_create(
            vendor=self,
            defaults={'commission': commission}
        )

        if not created and assignment.commission != commission:
            assignment.commission = commission
            assignment.save()

    def reject(self, rejected_by_user, notes=""):
        """Reject the vendor"""
        self.approval_status = 'rejected'
        self.approved_by = rejected_by_user
        self.approval_notes = notes
        self.save()

        # Send rejection email
        subject = "Your Vendor Application Has Been Rejected"
        context = {
            'vendor': self,
            'notes': notes,
        }
        html_message = render_to_string('emails/vendor_rejected.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            fail_silently=False,
        )

    def create_user_profile(self):
        """Create User and UserProfile when vendor is approved"""
        if self.approval_status == 'approved':
            raw_password = "1234"


            user = User.objects.create_user(
                username=f"vendor_{self.id}_{self.phone}",
                email=self.email,
                password=raw_password
            )

            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                account_type='4',
                Coach_profile=self,
                is_active=True
            )

            user.raw_password = raw_password
            return user
        return None


class ReceptionistProfile(models.Model):
    STATUS_CHOICES = [
        ('free', 'Free'),
        ('busy', 'Busy'),
        ('hold', 'On Hold'),
    ]
    full_name = models.CharField(max_length=50)
    profile_image_base64 = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    club = models.ForeignKey('ClubsModel', on_delete=models.SET_NULL, null=True)
    about = models.TextField(null=True, blank=True)
    hire_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='free')
    last_assignment_time = models.DateTimeField(null=True, blank=True)
    hold_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Receptionist: {self.full_name}"

    def is_available(self):
        if self.status == 'hold':
            return self.hold_until and timezone.now() > self.hold_until
        return self.status == 'free'

    def set_status(self, status, hold_minutes=None):
        self.status = status
        if status == 'hold' and hold_minutes:
            self.hold_until = timezone.now() + timedelta(minutes=hold_minutes)
        self.save()



class AccountantProfile(models.Model):
    full_name = models.CharField(max_length=50)
    profile_image_base64 = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    club = models.ForeignKey('ClubsModel', on_delete=models.SET_NULL, null=True)
    about = models.TextField(null=True, blank=True)
    hire_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.hire_date = timezone.now()
        super(AccountantProfile, self).save(*args, **kwargs)

    def __str__(self):
        return f"Accountant: {self.full_name}"



class AdministrativeProfile(models.Model):
    full_name = models.CharField(max_length=50)
    profile_image_base64 = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50)
    about = models.TextField(null=True, blank=True)
    email = models.EmailField()
    # ✅ Ensure multiple administrators per club
    club = models.ForeignKey('ClubsModel', on_delete=models.CASCADE, related_name="administrators")

    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.club.name}"


# models.py - Add this to your existing models

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class OTP(models.Model):
    DELIVERY_METHODS = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_METHODS,
        default='email'
    )
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.username} - {self.otp_code}"

    def is_expired(self):
        """Check if OTP is expired (5 minutes)"""
        return timezone.now() - self.created_at > timedelta(minutes=5)

    def is_valid(self):
        """Check if OTP is valid (not expired and not used)"""
        return not self.is_expired() and not self.is_used


# Add this to your models.py file

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Subscription(models.Model):
    PLAN_CHOICES = [
        ('1', 'Free Plan'),
        ('2', 'Basic Plan'),
        ('3', 'Advanced Plan'),
        ('4', 'Premium Plan'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    club = models.ForeignKey('ClubsModel', on_delete=models.CASCADE, related_name='subscriptions')
    plan_id = models.CharField(max_length=10, choices=PLAN_CHOICES, default='1')
    plan_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.plan_name} ({self.status})"

    @property
    def is_active(self):
        return self.status == 'active' and self.end_date > timezone.now()

    @property
    def days_remaining(self):
        if self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0

    def extend_subscription(self, days=30):
        """Extend subscription by specified days"""
        if self.end_date < timezone.now():
            # If expired, start from now
            self.end_date = timezone.now() + timedelta(days=days)
        else:
            # If active, extend from current end date
            self.end_date += timedelta(days=days)
        self.save()

    @classmethod
    def get_active_subscription(cls, user):
        """Get the active subscription for a user"""
        return cls.objects.filter(
            user=user,
            status='active',
            end_date__gt=timezone.now()
        ).first()

    @classmethod
    def create_subscription(cls, user, club, plan_data, payment_reference=None, duration_days=30):
        """Create a new subscription"""
        end_date = timezone.now() + timedelta(days=duration_days)

        # Deactivate previous subscriptions
        cls.objects.filter(user=user, status='active').update(status='expired')

        return cls.objects.create(
            user=user,
            club=club,
            plan_id=str(plan_data['id']),
            plan_name=plan_data['name'],
            amount=plan_data.get('amount', 0.0),
            payment_reference=payment_reference,
            status='active',
            end_date=end_date
        )

class DashboardSettings(models.Model):
    club = models.OneToOneField(ClubsModel, on_delete=models.CASCADE, related_name='dashboard_settings')
    show_employee_client_counts = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dashboard Settings for {self.club.name}"

class PasswordResetToken(models.Model):
    """Model to store password reset tokens"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'

    def __str__(self):
        return f"Reset token for {self.user.username}"

    def is_expired(self):
        """Check if token is expired"""
        return timezone.now() > self.expires_at