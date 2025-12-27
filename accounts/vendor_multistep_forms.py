import base64
import re
from django import forms
from .models import CoachProfile
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class VendorStep1Form(forms.Form):
    """Step 1: Personal Information with comprehensive validation"""

    full_name = forms.CharField(
        label="الاسم الكامل",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'الاسم الكامل',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True,
            'minlength': '3',
            'maxlength': '100'
        })
    )

    phone = forms.CharField(
        label="رقم الهاتف",
        max_length=15,
        widget=forms.TextInput(attrs={
            'placeholder': '5XXXXXXXX',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True,
            'pattern': '^5[0-9]{8}$',
            'title': 'يرجى إدخال رقم جوال سعودي صحيح يبدأ بـ 5 ومكون من 9 أرقام',
            'maxlength': '9',
            'dir': 'ltr'
        })
    )

    email = forms.EmailField(
        label="البريد الإلكتروني",
        widget=forms.EmailInput(attrs={
            'placeholder': 'example@domain.com',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True,
            'type': 'email',
            'dir': 'ltr'
        })
    )

    def clean_full_name(self):
        """Validate full name"""
        full_name = self.cleaned_data.get('full_name', '').strip()

        if not full_name:
            raise ValidationError("الاسم الكامل مطلوب")

        if len(full_name) < 3:
            raise ValidationError("الاسم يجب أن يكون 3 أحرف على الأقل")

        if len(full_name) > 100:
            raise ValidationError("الاسم يجب ألا يزيد عن 100 حرف")

        # Check if name contains only letters, spaces, and Arabic/English characters
        if not re.match(r'^[\u0600-\u06FFa-zA-Z\s]+$', full_name):
            raise ValidationError("الاسم يجب أن يحتوي على حروف فقط")

        # Check for at least two words (first name and last name)
        words = full_name.split()
        if len(words) < 2:
            raise ValidationError("يرجى إدخال الاسم الأول واسم العائلة على الأقل")

        return full_name

    def clean_phone(self):
        """Validate Saudi Arabian phone number"""
        phone = self.cleaned_data.get('phone', '').strip()

        # Remove any spaces, dashes, or parentheses
        phone = re.sub(r'[\s\-\(\)\+]', '', phone)

        # Remove country code if present
        if phone.startswith('966'):
            phone = phone[3:]
        elif phone.startswith('00966'):
            phone = phone[5:]
        elif phone.startswith('+966'):
            phone = phone[4:]

        # Remove leading zero if present
        if phone.startswith('0'):
            phone = phone[1:]

        # Validate Saudi phone number format (must start with 5 and be 9 digits)
        if not re.match(r'^5[0-9]{8}$', phone):
            raise ValidationError(
                "رقم الجوال غير صحيح. يجب أن يبدأ بـ 5 ويتكون من 9 أرقام (مثال: 512345678)"
            )

        # Check if phone number already exists
        if CoachProfile.objects.filter(phone=phone).exists():
            raise ValidationError("رقم الهاتف مسجل مسبقاً")

        return phone

    def clean_email(self):
        """Validate email"""
        email = self.cleaned_data.get('email', '').strip().lower()

        if not email:
            raise ValidationError("البريد الإلكتروني مطلوب")

        # Basic email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError("البريد الإلكتروني غير صحيح")

        # Check if email already exists
        if CoachProfile.objects.filter(email=email).exists():
            raise ValidationError("البريد الإلكتروني مسجل مسبقاً")

        # Check if email exists in User model
        if User.objects.filter(email=email).exists():
            raise ValidationError("البريد الإلكتروني مسجل مسبقاً")

        return email


class VendorStep2Form(forms.Form):
    """Step 2: Business Information with comprehensive validation"""

    business_name_ar = forms.CharField(
        label="اسم النشاط التجاري (عربي)",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'اسم النشاط التجاري (عربي)',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True,
            'minlength': '3',
            'maxlength': '100',
            'dir': 'rtl'
        })
    )

    business_name_en = forms.CharField(
        label="Business Name (English)",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Business Name (English)',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True,
            'minlength': '3',
            'maxlength': '100',
            'dir': 'ltr'
        })
    )

    activity_type = forms.ChoiceField(
        choices=[],
        label="نوع النشاط",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True
        })
    )

    number_of_branches = forms.IntegerField(
        label="عدد الفروع",
        min_value=1,
        max_value=1000,
        widget=forms.NumberInput(attrs={
            'placeholder': 'عدد الفروع',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'min': '1',
            'max': '1000',
            'required': True
        })
    )

    description = forms.CharField(
        label="وصف الخدمة",
        widget=forms.Textarea(attrs={
            'placeholder': 'اكتب وصفاً تفصيلياً عن الخدمات التي تقدمها (الحد الأدنى 50 حرف)',
            'rows': 4,
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True,
            'minlength': '50',
            'maxlength': '1000'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from club_dashboard.models import Category
        categories = Category.objects.filter(is_active=True)

        # Set choices for the ChoiceField
        category_choices = [('', 'اختر نوع النشاط')]
        category_choices.extend([(str(cat.id), cat.name) for cat in categories])

        self.fields['activity_type'].choices = category_choices

    def clean_business_name_ar(self):
        """Validate Arabic business name"""
        name = self.cleaned_data.get('business_name_ar', '').strip()

        if not name:
            raise ValidationError("اسم النشاط بالعربي مطلوب")

        if len(name) < 3:
            raise ValidationError("اسم النشاط يجب أن يكون 3 أحرف على الأقل")

        if len(name) > 100:
            raise ValidationError("اسم النشاط يجب ألا يزيد عن 100 حرف")

        # Check if contains Arabic characters
        if not re.search(r'[\u0600-\u06FF]', name):
            raise ValidationError("اسم النشاط بالعربي يجب أن يحتوي على أحرف عربية")

        return name

    def clean_business_name_en(self):
        """Validate English business name"""
        name = self.cleaned_data.get('business_name_en', '').strip()

        if not name:
            raise ValidationError("Business name in English is required")

        if len(name) < 3:
            raise ValidationError("Business name must be at least 3 characters")

        if len(name) > 100:
            raise ValidationError("Business name must not exceed 100 characters")

        # Check if contains English characters
        if not re.search(r'[a-zA-Z]', name):
            raise ValidationError("Business name in English must contain English letters")

        return name

    def clean_activity_type(self):
        """Validate activity type"""
        activity_type = self.cleaned_data.get('activity_type')

        if not activity_type:
            raise ValidationError("نوع النشاط مطلوب")

        # Validate that category exists
        from club_dashboard.models import Category
        try:
            Category.objects.get(id=activity_type, is_active=True)
        except Category.DoesNotExist:
            raise ValidationError("نوع النشاط المختار غير صحيح")

        return activity_type

    def clean_number_of_branches(self):
        """Validate number of branches"""
        branches = self.cleaned_data.get('number_of_branches')

        if branches is None:
            raise ValidationError("عدد الفروع مطلوب")

        if branches < 1:
            raise ValidationError("عدد الفروع يجب أن يكون على الأقل 1")

        if branches > 1000:
            raise ValidationError("عدد الفروع يجب ألا يزيد عن 1000")

        return branches

    def clean_description(self):
        """Validate description"""
        description = self.cleaned_data.get('description', '').strip()

        if not description:
            raise ValidationError("وصف الخدمة مطلوب")

        if len(description) < 50:
            raise ValidationError("وصف الخدمة يجب أن يكون 50 حرف على الأقل")

        if len(description) > 1000:
            raise ValidationError("وصف الخدمة يجب ألا يزيد عن 1000 حرف")

        return description


class VendorStep3Form(forms.Form):
    """Step 3: Location & Registration with comprehensive validation"""

    region = forms.ChoiceField(
        choices=[],
        label="المنطقة",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'id': 'region-select',
            'required': True
        })
    )

    city = forms.ChoiceField(
        choices=[],
        label="المدينة",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'id': 'city-select',
            'required': True
        })
    )

    district = forms.CharField(
        label="الحي",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'الحي',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True,
            'minlength': '2',
            'maxlength': '100'
        })
    )

    street = forms.CharField(
        label="الشارع",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'الشارع',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True,
            'minlength': '2',
            'maxlength': '100'
        })
    )

    business_document_type = forms.ChoiceField(
        choices=[
            ('', 'اختر نوع الوثيقة'),
            ('freelance', 'العمل الحر'),
            ('commercial_register', 'السجل التجاري'),
        ],
        label="نوع الوثيقة التجارية",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True
        })
    )

    commercial_registration_number = forms.CharField(
        label="رقم السجل التجاري (10 أرقام)",
        max_length=10,
        widget=forms.TextInput(attrs={
            'placeholder': '1234567890',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'maxlength': '10',
            'minlength': '10',
            'pattern': '[0-9]{10}',
            'title': 'رقم السجل التجاري يجب أن يكون 10 أرقام بالضبط',
            'required': True,
            'dir': 'ltr'
        })
    )

    tax_number = forms.CharField(
        label="الرقم الضريبي (اختياري)",
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '123456789012345',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'maxlength': '15',
            'pattern': '[0-9]{15}',
            'title': 'الرقم الضريبي يجب أن يكون 15 رقماً',
            'dir': 'ltr'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .fields import REGIONS_AND_CITIES

        # Set initial region choices
        self.fields['region'].choices = [('', 'اختر المنطقة')] + [(r, r) for r in REGIONS_AND_CITIES.keys()]

        # Set initial city choices based on data if available
        if self.data.get('region'):
            region = self.data.get('region')
            if region in REGIONS_AND_CITIES:
                self.fields['city'].choices = [('', 'اختر المدينة')] + [(c, c) for c in REGIONS_AND_CITIES[region]]
        elif self.initial.get('region'):
            region = self.initial.get('region')
            if region in REGIONS_AND_CITIES:
                self.fields['city'].choices = [('', 'اختر المدينة')] + [(c, c) for c in REGIONS_AND_CITIES[region]]
        else:
            self.fields['city'].choices = [('', 'اختر المدينة')]

    def clean_region(self):
        """Validate region"""
        region = self.cleaned_data.get('region')

        if not region:
            raise ValidationError("المنطقة مطلوبة")

        from .fields import REGIONS_AND_CITIES
        if region not in REGIONS_AND_CITIES.keys():
            raise ValidationError("المنطقة المختارة غير صحيحة")

        return region

    def clean_city(self):
        """Validate city"""
        city = self.cleaned_data.get('city')

        if not city:
            raise ValidationError("المدينة مطلوبة")

        return city

    def clean_district(self):
        """Validate district"""
        district = self.cleaned_data.get('district', '').strip()

        if not district:
            raise ValidationError("الحي مطلوب")

        if len(district) < 2:
            raise ValidationError("اسم الحي يجب أن يكون حرفين على الأقل")

        if len(district) > 100:
            raise ValidationError("اسم الحي يجب ألا يزيد عن 100 حرف")

        return district

    def clean_street(self):
        """Validate street"""
        street = self.cleaned_data.get('street', '').strip()

        if not street:
            raise ValidationError("الشارع مطلوب")

        if len(street) < 2:
            raise ValidationError("اسم الشارع يجب أن يكون حرفين على الأقل")

        if len(street) > 100:
            raise ValidationError("اسم الشارع يجب ألا يزيد عن 100 حرف")

        return street

    def clean_business_document_type(self):
        """Validate business document type"""
        doc_type = self.cleaned_data.get('business_document_type')

        if not doc_type:
            raise ValidationError("نوع الوثيقة التجارية مطلوب")

        valid_types = ['freelance', 'commercial_register']
        if doc_type not in valid_types:
            raise ValidationError("نوع الوثيقة المختار غير صحيح")

        return doc_type

    def clean_commercial_registration_number(self):
        """Validate commercial registration number"""
        number = self.cleaned_data.get('commercial_registration_number', '').strip()

        if not number:
            raise ValidationError("رقم السجل التجاري مطلوب")

        # Remove any spaces or dashes
        number = re.sub(r'[\s\-]', '', number)

        # Check if it's exactly 10 digits
        if not re.match(r'^\d{10}$', number):
            raise ValidationError("رقم السجل التجاري يجب أن يكون 10 أرقام بالضبط")

        # Check if already exists
        if CoachProfile.objects.filter(commercial_registration_number=number).exists():
            raise ValidationError("رقم السجل التجاري مسجل مسبقاً")

        return number

    def clean_tax_number(self):
        """Validate tax number (optional)"""
        number = self.cleaned_data.get('tax_number', '').strip()

        if not number:
            return ''

        # Remove any spaces or dashes
        number = re.sub(r'[\s\-]', '', number)

        # Check if it's exactly 15 digits
        if number and not re.match(r'^\d{15}$', number):
            raise ValidationError("الرقم الضريبي يجب أن يكون 15 رقماً بالضبط")

        return number

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        city = cleaned_data.get('city')

        # Validate city belongs to selected region
        if region and city:
            from .fields import REGIONS_AND_CITIES
            valid_cities = REGIONS_AND_CITIES.get(region, [])
            if city not in valid_cities:
                raise forms.ValidationError(
                    f"المدينة {city} غير موجودة في المنطقة {region}"
                )

        return cleaned_data


class VendorStep4Form(forms.Form):
    """Step 4: Documents & Verification with comprehensive validation"""

    business_document_file = forms.FileField(
        label="ملف الوثيقة التجارية",
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'required': True
        })
    )

    commercial_registration_certificate = forms.FileField(
        label="شهادة السجل التجاري",
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'required': True
        })
    )

    tax_certificate = forms.FileField(
        label="شهادة الرقم الضريبي (اختياري)",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )

    store_logo = forms.FileField(
        label="شعار المتجر",
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'accept': '.jpg,.jpeg,.png,.gif',
            'required': True
        })
    )

    accept_terms = forms.BooleanField(
        label="أوافق على سياسة الخصوصية وشروط الاستخدام",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2',
            'required': True
        })
    )

    def clean_business_document_file(self):
        """Validate business document file"""
        file = self.cleaned_data.get('business_document_file')

        if not file:
            raise ValidationError("ملف الوثيقة التجارية مطلوب")

        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("حجم الملف يجب أن يكون أقل من 5 ميجابايت")

        # Check file extension
        valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_extension = file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in valid_extensions:
            raise ValidationError("نوع الملف غير مدعوم. يرجى رفع ملف PDF أو صورة")

        return file

    def clean_commercial_registration_certificate(self):
        """Validate commercial registration certificate"""
        file = self.cleaned_data.get('commercial_registration_certificate')

        if not file:
            raise ValidationError("شهادة السجل التجاري مطلوبة")

        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("حجم الملف يجب أن يكون أقل من 5 ميجابايت")

        # Check file extension
        valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_extension = file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in valid_extensions:
            raise ValidationError("نوع الملف غير مدعوم. يرجى رفع ملف PDF أو صورة")

        return file

    def clean_tax_certificate(self):
        """Validate tax certificate (optional)"""
        file = self.cleaned_data.get('tax_certificate')

        if not file:
            return None

        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("حجم الملف يجب أن يكون أقل من 5 ميجابايت")

        # Check file extension
        valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_extension = file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in valid_extensions:
            raise ValidationError("نوع الملف غير مدعوم. يرجى رفع ملف PDF أو صورة")

        return file

    def clean_store_logo(self):
        """Validate store logo"""
        file = self.cleaned_data.get('store_logo')

        if not file:
            raise ValidationError("شعار المتجر مطلوب")

        # Check file size (max 2MB for images)
        if file.size > 2 * 1024 * 1024:
            raise ValidationError("حجم الصورة يجب أن يكون أقل من 2 ميجابايت")

        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        file_extension = file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in valid_extensions:
            raise ValidationError("نوع الملف غير مدعوم. يرجى رفع صورة (JPG, PNG, GIF)")

        return file

    def clean_accept_terms(self):
        """Validate terms acceptance"""
        accept_terms = self.cleaned_data.get('accept_terms')

        if not accept_terms:
            raise ValidationError("يجب الموافقة على سياسة الخصوصية وشروط الاستخدام")

        return accept_terms


def handle_file_upload(file_field):
    """Convert uploaded file to base64 string"""
    if file_field:
        file_content = file_field.read()
        encoded_file = base64.b64encode(file_content).decode('utf-8')
        return encoded_file
    return None