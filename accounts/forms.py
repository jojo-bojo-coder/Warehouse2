import sys
import base64
from io import BytesIO
from django import forms
from .models import StudentProfile, ClubsModel,CoachProfile
from django.core.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.conf import settings


class StudentProfileForm(forms.ModelForm):
    """Form for creating/updating a student profile."""

    profile_image_base64 = forms.FileField(
        label="صورة الملف الشخصي",
        required=False,
        widget=forms.FileInput(attrs={
            'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
        })
    )

    class Meta:
        model = StudentProfile
        fields = ['full_name', 'phone', 'birthday', 'profile_image_base64']

        widgets = {
            'full_name': forms.TextInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ", 'placeholder': 'Full Name / الاسم الكامل'}),
            'phone': forms.TextInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500", 'placeholder': 'Phone Number / رقم الهاتف'}),
            'birthday': forms.DateInput(format=('%d-%m-%Y'), attrs={'type': 'date', 'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"}),
        }
        labels = {
            'full_name': 'الاسم الكامل',
            'phone': 'رقم الهاتف',
            'birthday': 'تاريخ الميلاد',
            'profile_image_base64': 'صورة الملف الشخصي',
        }

    def clean_profile_image_base64(self):
        """Convert uploaded image file to Base64 string before saving."""
        image_file = self.cleaned_data.get("profile_image_base64")

        if image_file:
            try:
                image_data = image_file.read()

                base64_encoded = base64.b64encode(image_data).decode("utf-8")
                return base64_encoded

            except Exception as e:
                print(f"ERROR: Failed to convert student profile image to Base64: {e}")
                raise forms.ValidationError(f"خطأ في معالجة الصورة: {e}")

        return None

    def save(self, commit=True):
        student = super().save(commit=False)

        # Automatically set the main club
        try:
            main_club = ClubsModel.objects.get(id=settings.MAIN_CLUB_ID)
            student.club = main_club
        except ClubsModel.DoesNotExist:
            # Fallback to first club if main club doesn't exist
            student.club = ClubsModel.objects.first()

        if 'profile_image_base64' in self.cleaned_data and self.cleaned_data['profile_image_base64']:
            student.profile_image_base64 = self.cleaned_data['profile_image_base64']

        if commit:
            student.save()
        return student


class DirectorSignupForm(forms.Form):
    """Form for Director signup, including club registration with Base64 image conversion."""

    # User fields
    username = forms.CharField(label="اسم المستخدم", widget=forms.TextInput(attrs={'class': "input-style"}))
    email = forms.EmailField(label="البريد الالكتروني", widget=forms.EmailInput(attrs={'class': "input-style"}))
    password = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput(attrs={'class': "input-style"}))
    phone = forms.CharField(label="رقم الهاتف", widget=forms.TextInput(attrs={'class': "input-style"}))

    # Club fields
    club_name = forms.CharField(label="اسم النادي", widget=forms.TextInput(attrs={'class': "input-style"}))
    city = forms.ChoiceField(label="المدينة", choices=[], widget=forms.Select(attrs={'class': "input-style"}))
    street = forms.CharField(label="الشارع", widget=forms.TextInput(attrs={'class': "input-style"}))
    district = forms.CharField(label="الحي", required=False, widget=forms.TextInput(attrs={'class': "input-style"}))
    about = forms.CharField(label="عن النادي", required=False, widget=forms.Textarea(attrs={'class': "input-style", 'rows': 3}))
    desc = forms.CharField(label="وصف قصير", required=False, widget=forms.Textarea(attrs={'class': "input-style", 'rows': 2}))
    club_profile_image_base64 = forms.FileField(label="شعار الصالون", required=False, widget=forms.FileInput(attrs={'class': "input-style"}))

    def __init__(self, *args, **kwargs):
        """Initialize form and handle city choices dynamically."""
        super().__init__(*args, **kwargs)

        # Import city choices dynamically to avoid circular import issues
        from .fields import citys

        # Ensure `citys` is a valid tuple and has data
        if not isinstance(citys, tuple) or not citys:
            citys = (('', 'اختر المدينة'),)  # Safe fallback as a tuple

        # Convert tuple to list before assigning (Django requires lists for choices)
        self.fields['city'].choices = list(citys)

    def clean_club_profile_image_base64(self):
        """Convert uploaded image file to Base64 string before saving."""
        image_file = self.cleaned_data.get("club_profile_image_base64")

        if image_file:
            try:
                # Read image binary data
                image_data = image_file.read()

                # Debugging: Print first 50 bytes of the image
                print(f"DEBUG: First 50 bytes of image = {image_data[:50]}")

                # Encode to Base64
                base64_encoded = base64.b64encode(image_data).decode("utf-8")
                print(f"DEBUG: Base64 length = {len(base64_encoded)}")

                return base64_encoded

            except Exception as e:
                print(f"ERROR: Failed to convert image to Base64: {e}")
                raise forms.ValidationError(f"خطأ في معالجة الصورة: {e}")

        return None  # No image uploaded


class EditClubProfileForm(forms.ModelForm):
    """Form for editing club profile with Base64 image handling."""

    club_profile_image_base64 = forms.FileField(label="شعار النادي", required=False, widget=forms.FileInput(attrs={'class': "input-style"}))

    class Meta:
        model = ClubsModel
        fields = ['name', 'desc', 'about', 'club_profile_image_base64']

    def save(self, commit=True):
        club = super().save(commit=False)

        # Handle image upload and Base64 conversion
        if self.cleaned_data.get('club_profile_image_base64'):
            image = self.cleaned_data['club_profile_image_base64']
            image_data = image.read()
            base64_encoded = base64.b64encode(image_data).decode('utf-8')
            club.club_profile_image_base64 = base64_encoded

        if commit:
            club.save()
        return club

class ReceptionistSignupForm(forms.Form):
    """Form for Receptionist signup."""

    # User fields
    username = forms.CharField(label="اسم المستخدم", widget=forms.TextInput(attrs={'class': "input-style"}))
    email = forms.EmailField(label="البريد الالكتروني", widget=forms.EmailInput(attrs={'class': "input-style"}))
    password = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500",'placeholder': 'أدخل كلمة المرور'}))

    # Receptionist fields
    full_name = forms.CharField(label="الاسم الكامل", widget=forms.TextInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500",'placeholder': 'الاسم كامل'}))
    phone = forms.CharField(label="رقم الهاتف", widget=forms.TextInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500",'placeholder': 'رقم الهاتف'}))
    club = forms.ModelChoiceField(
        queryset=ClubsModel.objects.all(),
        label="النادي",
        widget=forms.Select(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"})
    )
    about = forms.CharField(
        label="معلومات إضافية",
        required=False,
        widget=forms.Textarea(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500", 'rows': 3, 'placeholder': 'معلومات إضافية'})
    )

class AdministratorSignupForm(forms.Form):
    """Form for Administrator signup."""

    # User fields
    username = forms.CharField(label="اسم المستخدم", widget=forms.TextInput(attrs={'class': "input-style"}))
    email = forms.EmailField(label="البريد الالكتروني", widget=forms.EmailInput(attrs={'class': "input-style"}))
    password = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500",'placeholder': 'أدخل كلمة المرور'}))

    # Receptionist fields
    full_name = forms.CharField(label="الاسم الكامل", widget=forms.TextInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500",'placeholder': 'الاسم كامل'}))
    phone = forms.CharField(label="رقم الهاتف", widget=forms.TextInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500",'placeholder': 'رقم الهاتف'}))
    club = forms.ModelChoiceField(
        queryset=ClubsModel.objects.all(),
        label="النادي",
        widget=forms.Select(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"})
    )
    about = forms.CharField(
        label="معلومات إضافية",
        required=False,
        widget=forms.Textarea(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500", 'rows': 3, 'placeholder': 'معلومات إضافية'})
    )

class ForgotPasswordForm(forms.Form):
    """Form for requesting password reset"""

    email = forms.EmailField(
        label="البريد الإلكتروني",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 pl-12 rounded-lg border border-indigo-200 focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 placeholder-indigo-300 text-indigo-800 transition-all',
            'placeholder': 'أدخل بريدك الإلكتروني',
            'required': True
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
        return email

class ResetPasswordForm(forms.Form):
    """Form for resetting password with new password"""

    new_password = forms.CharField(
        label="كلمة المرور الجديدة",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 pl-12 rounded-lg border border-indigo-200 focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 placeholder-indigo-300 text-indigo-800 transition-all',
            'placeholder': 'أدخل كلمة المرور الجديدة',
            'required': True
        })
    )

    confirm_password = forms.CharField(
        label="تأكيد كلمة المرور",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 pl-12 rounded-lg border border-indigo-200 focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 placeholder-indigo-300 text-indigo-800 transition-all',
            'placeholder': 'أعد إدخال كلمة المرور الجديدة',
            'required': True
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError({
                    'confirm_password': 'كلمات المرور غير متطابقة.'
                })

            if len(new_password) < 8:
                raise ValidationError({
                    'new_password': 'كلمة المرور يجب أن تكون 8 أحرف على الأقل.'
                })

        return cleaned_data


class VendorRegistrationForm(forms.ModelForm):
    # Business document file field
    business_document_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'input-style',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'id': 'business_document_file'
        }),
        label="ملف الوثيقة التجارية"
    )

    # Commercial Registration Certificate
    commercial_registration_certificate = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'input-style',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'id': 'commercial_registration_certificate'
        }),
        label="شهادة السجل التجاري"
    )

    # Tax Certificate (optional)
    tax_certificate = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'input-style',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'id': 'tax_certificate'
        }),
        label="شهادة الرقم الضريبي (اختياري)"
    )

    # Store Logo
    store_logo = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'input-style',
            'accept': '.jpg,.jpeg,.png,.gif',
            'id': 'store_logo'
        }),
        label="شعار المتجر"
    )

    # Add terms acceptance checkbox
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'mr-2'
        }),
        label="أوافق على سياسة الخصوصية وشروط الاستخدام"
    )

    region = forms.ChoiceField(
        choices=[],
        label="المنطقة",
        widget=forms.Select(attrs={'class': 'input-style', 'id': 'region-select'})
    )

    city = forms.ChoiceField(
        choices=[],
        label="المدينة",
        widget=forms.Select(attrs={'class': 'input-style', 'id': 'city-select'})
    )



    class Meta:
        model = CoachProfile
        fields = [
            'region', 'city',
            'full_name',
            'phone',
            'email',
            'activity_type',
            'district',
            'street',
            'business_name_en',
            'business_name_ar',
            'number_of_branches',
            'description',
            'business_document_type',
            'commercial_registration_number',
            'tax_number',
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'الاسم الكامل',
                'class': 'input-style'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'رقم الهاتف',
                'class': 'input-style'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'البريد الإلكتروني',
                'class': 'input-style'
            }),
            'activity_type': forms.Select(attrs={
                'class': 'input-style'
            }),
            'district': forms.TextInput(attrs={
                'placeholder': 'الحي',
                'class': 'input-style'
            }),
            'street': forms.TextInput(attrs={
                'placeholder': 'الشارع',
                'class': 'input-style'
            }),
            'business_name_en': forms.TextInput(attrs={
                'placeholder': 'Business Name (English)',
                'class': 'input-style'
            }),
            'business_name_ar': forms.TextInput(attrs={
                'placeholder': 'اسم النشاط التجاري (عربي)',
                'class': 'input-style'
            }),
            'number_of_branches': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-blue-50 transition-all duration-300 hover:bg-blue-50 hover:border-blue-400',
                'placeholder': 'Number of Branches',
                'min': 1
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'وصف الخدمة',
                'rows': 4,
                'class': 'input-style'
            }),
            'business_document_type': forms.Select(attrs={
                'class': 'input-style',
                'id': 'business_document_type'
            }),
            'commercial_registration_number': forms.TextInput(attrs={
                'placeholder': 'رقم السجل التجاري (10 أرقام)',
                'class': 'input-style',
                'maxlength': '10',
                'pattern': '[0-9]{10}',
                'title': 'يجب أن يكون 10 أرقام بالضبط'
            }),
            'tax_number': forms.TextInput(attrs={
                'placeholder': 'الرقم الضريبي (15 رقم - اختياري)',
                'class': 'input-style',
                'maxlength': '15',
                'pattern': '[0-9]{15}',
                'title': 'يجب أن يكون 15 رقم بالضبط إذا تم إدخاله'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .fields import REGIONS_AND_CITIES

        # Set initial values for required fields
        self.fields['business_name_en'].initial = "Unspecified Business"
        self.fields['business_name_ar'].initial = "نشاط غير محدد"
        self.fields['number_of_branches'].initial = 1

        # Set region choices
        self.fields['region'].choices = [('', 'اختر المنطقة')] + [(r, r) for r in REGIONS_AND_CITIES.keys()]

        # Set city choices based on initial region if available
        if 'region' in self.data:
            try:
                region = self.data.get('region')
                if region in REGIONS_AND_CITIES:
                    self.fields['city'].choices = [('', 'اختر المدينة')] + [(c, c) for c in REGIONS_AND_CITIES[region]]
            except (ValueError, TypeError):
                pass
        else:
            self.fields['city'].choices = [('', 'اختر المدينة')]


        from club_dashboard.models import Category

        # Get active categories
        categories = Category.objects.filter(is_active=True)

        # Set choices for the field
        category_choices = [('', 'اختر نوع النشاط')]  # Empty choice
        category_choices.extend([(cat.id, cat.name) for cat in categories])

        self.fields['activity_type'].choices = category_choices
        self.fields['activity_type'].label = "نوع النشاط"
        self.fields['activity_type'].required = True

        # Update the widget
        self.fields['activity_type'].widget = forms.Select(
            attrs={'class': 'input-style'},
            choices=category_choices
        )

        # Make required fields except optional ones
        for field_name, field in self.fields.items():
            if field_name not in ['description', 'tax_number', 'tax_certificate']:
                field.required = True

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
        if number and not number.isdigit():
            raise forms.ValidationError('رقم السجل التجاري يجب أن يحتوي على أرقام فقط')
        if number and len(number) != 10:
            raise forms.ValidationError('رقم السجل التجاري يجب أن يكون 10 أرقام بالضبط')
        return number

    def clean_tax_number(self):
        number = self.cleaned_data.get('tax_number')
        if number:
            if not number.isdigit():
                raise forms.ValidationError('الرقم الضريبي يجب أن يحتوي على أرقام فقط')
            if len(number) != 15:
                raise forms.ValidationError('الرقم الضريبي يجب أن يكون 15 رقم بالضبط')
        return number



class VendorApprovalForm(forms.Form):
    """Form for directors to approve/reject vendors"""
    action = forms.ChoiceField(
        choices=[
            ('approve', 'موافقة'),
            ('reject', 'رفض')
        ],
        widget=forms.RadioSelect()
    )

    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'ملاحظات (اختياري)',
            'rows': 3,
            'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
        }),
        required=False,
        label="ملاحظات"
    )