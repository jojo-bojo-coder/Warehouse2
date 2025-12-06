import base64
from django import forms
from .models import CoachProfile
from django.core.exceptions import ValidationError


class VendorStep1Form(forms.Form):
    """Step 1: Personal Information"""

    full_name = forms.CharField(
        label="الاسم الكامل",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'الاسم الكامل',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True
        })
    )

    phone = forms.CharField(
        label="رقم الهاتف",
        max_length=15,
        widget=forms.TextInput(attrs={
            'placeholder': 'رقم الهاتف',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True
        })
    )

    email = forms.EmailField(
        label="البريد الإلكتروني",
        widget=forms.EmailInput(attrs={
            'placeholder': 'البريد الإلكتروني',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CoachProfile.objects.filter(email=email).exists():
            raise ValidationError("البريد الإلكتروني مسجل مسبقاً")
        return email


class VendorStep2Form(forms.Form):
    """Step 2: Business Information"""

    business_name_ar = forms.CharField(
        label="اسم النشاط التجاري (عربي)",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'اسم النشاط التجاري (عربي)',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True
        })
    )

    business_name_en = forms.CharField(
        label="Business Name (English)",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Business Name (English)',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True
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
        widget=forms.NumberInput(attrs={
            'placeholder': 'عدد الفروع',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'min': 1,
            'required': True
        })
    )

    description = forms.CharField(
        label="وصف الخدمة",
        widget=forms.Textarea(attrs={
            'placeholder': 'وصف الخدمة',
            'rows': 4,
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from club_dashboard.models import Category
        categories = Category.objects.filter(is_active=True)

        # Set choices for the ChoiceField
        category_choices = [('', 'اختر نوع النشاط')]  # Empty choice
        category_choices.extend([(str(cat.id), cat.name) for cat in categories])

        self.fields['activity_type'].choices = category_choices
        self.fields['activity_type'].label = "نوع النشاط"
        self.fields['activity_type'].required = True


class VendorStep3Form(forms.Form):
    """Step 3: Location & Registration"""

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
            'required': True
        })
    )

    street = forms.CharField(
        label="الشارع",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'الشارع',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'required': True
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
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2' ,
            'required': True
        })
    )

    commercial_registration_number = forms.CharField(
        label="رقم السجل التجاري (10 أرقام)",
        max_length=10,
        widget=forms.TextInput(attrs={
            'placeholder': 'رقم السجل التجاري (10 أرقام)',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'maxlength': '10',
            'pattern': '[0-9]{10}',
            'required': True
        })
    )

    tax_number = forms.CharField(
        label="الرقم الضريبي (اختياري)",
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'الرقم الضريبي (اختياري)',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300 mt-2',
            'maxlength': '15'
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

    def clean(self):
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

    def clean_commercial_registration_number(self):
        number = self.cleaned_data.get('commercial_registration_number')
        if number and (not number.isdigit() or len(number) != 10):
            raise ValidationError("رقم السجل التجاري يجب أن يكون 10 أرقام بالضبط")
        return number


class VendorStep4Form(forms.Form):
    """Step 4: Documents & Verification"""

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
        file = self.cleaned_data.get('business_document_file')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError("حجم الملف يجب أن يكون أقل من 5 ميجابايت")
        return file

    def clean_commercial_registration_certificate(self):
        file = self.cleaned_data.get('commercial_registration_certificate')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError("حجم الملف يجب أن يكون أقل من 5 ميجابايت")
        return file

    def clean_store_logo(self):
        file = self.cleaned_data.get('store_logo')
        if file:
            if file.size > 2 * 1024 * 1024:  # 2MB limit for images
                raise ValidationError("حجم الصورة يجب أن يكون أقل من 2 ميجابايت")
        return file


def handle_file_upload(file_field):
    """Convert uploaded file to base64 string"""
    if file_field:
        file_content = file_field.read()
        encoded_file = base64.b64encode(file_content).decode('utf-8')
        return encoded_file
    return None

