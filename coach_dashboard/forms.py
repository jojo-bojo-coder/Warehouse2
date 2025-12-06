from django import forms
from accounts.models import CoachProfile

class CoachProfileForm(forms.ModelForm):
    class Meta:
        model = CoachProfile
        fields = [
            'full_name', 'phone', 'email', 'activity_type',
            'business_name_en', 'business_name_ar','number_of_branches', 'description', 'business_document_type',
            'city', 'district', 'street'
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-rose-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-300 focus:border-rose-400 transition-all duration-200',
                'placeholder': 'أدخل الاسم الكامل'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-rose-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-300 focus:border-rose-400 transition-all duration-200',
                'placeholder': 'أدخل رقم الهاتف'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-rose-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-300 focus:border-rose-400 transition-all duration-200',
                'placeholder': 'أدخل البريد الإلكتروني'
            }),
            'activity_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-rose-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-300 focus:border-rose-400 transition-all duration-200 bg-white cursor-pointer'
            }),
            'business_name_en': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-blue-50 transition-all duration-300 hover:bg-blue-50 hover:border-blue-400',
                'placeholder': 'Business Name (English)'
            }),
            'business_name_ar': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-blue-50 transition-all duration-300 hover:bg-blue-50 hover:border-blue-400',
                'placeholder': 'اسم النشاط التجاري (عربي)'
            }),
            'number_of_branches': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-blue-50 transition-all duration-300 hover:bg-blue-50 hover:border-blue-400',
                'placeholder': 'Number of Branches',
                'min': 1
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-rose-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-300 focus:border-rose-400 transition-all duration-200 min-h-[100px] resize-vertical',
                'placeholder': 'أدخل وصف الخدمة',
                'rows': 4
            }),
            'business_document_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-rose-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-300 focus:border-rose-400 transition-all duration-200 bg-white cursor-pointer'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-rose-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-300 focus:border-rose-400 transition-all duration-200',
                'placeholder': 'أدخل المدينة'
            }),
            'district': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-rose-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-300 focus:border-rose-400 transition-all duration-200',
                'placeholder': 'أدخل الحي'
            }),
            'street': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-rose-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-300 focus:border-rose-400 transition-all duration-200',
                'placeholder': 'أدخل الشارع'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make some fields required
        self.fields['full_name'].required = True
        self.fields['phone'].required = True
        self.fields['email'].required = True
        self.fields['business_name_en'].required = True
        self.fields['activity_type'].required = True

        # Add custom validation messages
        self.fields['email'].error_messages = {
            'invalid': 'يرجى إدخال بريد إلكتروني صحيح',
            'required': 'البريد الإلكتروني مطلوب'
        }

        self.fields['phone'].error_messages = {
            'required': 'رقم الهاتف مطلوب'
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.isdigit():
            raise forms.ValidationError('رقم الهاتف يجب أن يحتوي على أرقام فقط')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists for another coach
            existing_coach = CoachProfile.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance else None)
            if existing_coach.exists():
                raise forms.ValidationError('هذا البريد الإلكتروني مستخدم من قبل مدرب آخر')
        return email


from django import forms
from accounts.models import CoachProfile
from django.utils import timezone
import json
import base64


class BusinessProfileForm(forms.ModelForm):
    business_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'sr-only',
            'id': 'id_business_photo'
        })
    )

    class Meta:
        model = CoachProfile
        fields = [
            'business_name_en',
            'business_name_ar',
            'number_of_branches',
            'activity_type',
            'description',
            'business_document_type',
            'business_document_file',
            'whatsapp_business_number',
            'region',  # Add region field
            'city',
            'district',
            'street',
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white dark:hover:border-blue-500'
            }),
            'business_name_en': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'business_name_ar': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white dark:hover:border-blue-500'
            }),
            'activity_type': forms.Select(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'business_document_type': forms.Select(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'whatsapp_business_number': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'region': forms.Select(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'id': 'id_region'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'id': 'id_city'
            }),
            'district': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'street': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
        }
        labels = {
            'business_name_en': 'Business Name in EN',
            'business_name_ar': 'Business Name in Ar',
            'number_of_branches': 'Number of Branches',
            'activity_type': 'Activity Type',
            'description': 'Service Description',
            'business_document_type': 'Document Type',
            'business_document_file': 'Document File',
            'whatsapp_business_number': 'Business WhatsApp Number',
            'region': 'Region',
            'city': 'City',
            'district': 'District',
            'street': 'Street',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add required attribute to important fields
        self.fields['business_name_ar'].required = True
        self.fields['business_name_en'].required = True
        self.fields['activity_type'].required = True
        self.fields['region'].required = True  # Make region required

        # Set empty label for choice fields
        self.fields['business_document_type'].empty_label = "اختر نوع الوثيقة"
        self.fields['activity_type'].empty_label = "اختر نوع النشاط"
        self.fields['region'].empty_label = "اختر المنطقة"

    def clean_business_photo(self):
        """Validate business photo"""
        photo = self.cleaned_data.get('business_photo')
        if photo:
            # Check file size (max 10MB)
            if photo.size > 10 * 1024 * 1024:
                raise forms.ValidationError("حجم الصورة يجب أن يكون أقل من 10MB")

            # Check file type
            if not photo.content_type.startswith('image/'):
                raise forms.ValidationError("يجب أن يكون الملف صورة")

        return photo

    def clean(self):
        """Validate that the city belongs to the selected region"""
        from accounts.fields import REGIONS_AND_CITIES

        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        city = cleaned_data.get('city')

        if region and city:
            valid_cities = REGIONS_AND_CITIES.get(region, [])
            if city not in valid_cities:
                raise forms.ValidationError(
                    f"المدينة {city} غير موجودة في المنطقة {region}"
                )

        return cleaned_data

    def save(self, commit=True):
        coach = super().save(commit=False)

        # Handle business photo in the view, not here
        # The view will handle the base64 encoding

        if commit:
            coach.save()
        return coach

from accounts.models import CoachProfile
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
import base64
from django.utils import timezone


class PolicyDocumentsForm(forms.ModelForm):
    terms_conditions = forms.FileField(
        required=False,
        label="سياسة الشروط والأحكام",
        help_text="اختر ملفًا جديدًا لتحديث السياسة الحالية"
    )
    refund_policy = forms.FileField(
        required=False,
        label="سياسة الاسترجاع",
        help_text="اختر ملفًا جديدًا لتحديث السياسة الحالية"
    )

    class Meta:
        model = CoachProfile
        fields = []

    def save(self, commit=True):
        coach = super().save(commit=False)

        # Process Terms & Conditions if provided
        terms_file = self.cleaned_data.get('terms_conditions')
        if terms_file and isinstance(terms_file, InMemoryUploadedFile):
            encoded_terms = base64.b64encode(terms_file.read()).decode('utf-8')
            coach.policy_documents['terms_conditions'] = {
                'file': f"data:{terms_file.content_type};base64,{encoded_terms}",
                'uploaded_at': timezone.now().isoformat(),
                'filename': terms_file.name
            }

        # Process Refund Policy if provided
        refund_file = self.cleaned_data.get('refund_policy')
        if refund_file and isinstance(refund_file, InMemoryUploadedFile):
            encoded_refund = base64.b64encode(refund_file.read()).decode('utf-8')
            coach.policy_documents['refund_policy'] = {
                'file': f"data:{refund_file.content_type};base64,{encoded_refund}",
                'uploaded_at': timezone.now().isoformat(),
                'filename': refund_file.name
            }

        # Only mark as approved if both documents exist (either existing or newly uploaded)
        has_terms = 'terms_conditions' in coach.policy_documents
        has_refund = 'refund_policy' in coach.policy_documents
        coach.policies_approved = has_terms and has_refund

        if commit:
            coach.save()

        return coach



from django import forms
from .models import CoachReceptionistTicket, TicketMessage
from accounts.models import ReceptionistProfile
class CoachTicketForm(forms.ModelForm):
    class Meta:
        model = CoachReceptionistTicket
        fields = [ 'subject', 'message']
        labels = {
            'subject': 'Subject',
            'message': 'Message',
        }
        help_texts = {
            'subject': 'Write the subject of your support request',
            'message': 'Enter the details of your support request',
        }
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Write your message here...'
            }),
            'subject': forms.TextInput(attrs={
                'placeholder': 'Subject of the request'
            }),
        }

class TicketMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['message']
        labels = {
            'message': 'الرسالة',
        }
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'اكتب رسالتك هنا...'
            }),
        }


from django import forms
from django import forms
from .models import CoachProfile


class WorkingHoursForm(forms.ModelForm):
    DAYS_OF_WEEK = [
        ('monday', 'الإثنين'),
        ('tuesday', 'الثلاثاء'),
        ('wednesday', 'الأربعاء'),
        ('thursday', 'الخميس'),
        ('friday', 'الجمعة'),
        ('saturday', 'السبت'),
        ('sunday', 'الأحد'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add fields for each day
        for day, day_name in self.DAYS_OF_WEEK:
            self.fields[f'{day}_enabled'] = forms.BooleanField(
                required=False,
                label=f'تفعيل {day_name}',
                widget=forms.CheckboxInput(attrs={'class': 'toggle-input'})
            )
            self.fields[f'{day}_opening'] = forms.TimeField(
                required=False,
                label=f'وقت الفتح {day_name}',
                widget=forms.TimeInput(attrs={
                    'type': 'time',
                    'class': 'time-input'
                })
            )
            self.fields[f'{day}_closing'] = forms.TimeField(
                required=False,
                label=f'وقت الإغلاق {day_name}',
                widget=forms.TimeInput(attrs={
                    'type': 'time',
                    'class': 'time-input'
                })
            )

    class Meta:
        model = CoachProfile
        fields = ['is_working_hours_enabled']
        widgets = {
            'is_working_hours_enabled': forms.CheckboxInput(attrs={'class': 'toggle-input'})
        }

    def clean(self):
        cleaned_data = super().clean()

        # Validate that enabled days have both opening and closing times
        for day, day_name in self.DAYS_OF_WEEK:
            if cleaned_data.get(f'{day}_enabled'):
                opening = cleaned_data.get(f'{day}_opening')
                closing = cleaned_data.get(f'{day}_closing')

                if not opening:
                    raise forms.ValidationError(f'يجب تحديد وقت الفتح لـ {day_name}')
                if not closing:
                    raise forms.ValidationError(f'يجب تحديد وقت الإغلاق لـ {day_name}')

                # Check if closing time is after opening time
                if opening and closing and closing <= opening:
                    raise forms.ValidationError(f'وقت الإغلاق يجب أن يكون بعد وقت الفتح لـ {day_name}')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        working_hours = {}
        for day, day_name in self.DAYS_OF_WEEK:
            if self.cleaned_data.get(f'{day}_enabled'):
                opening_time = self.cleaned_data.get(f'{day}_opening')
                closing_time = self.cleaned_data.get(f'{day}_closing')

                if opening_time and closing_time:
                    working_hours[day] = {
                        'enabled': True,
                        'opening': opening_time.strftime('%H:%M'),
                        'closing': closing_time.strftime('%H:%M')
                    }

        instance.working_hours = working_hours

        if commit:
            instance.save()

        return instance


from django import forms
from django.utils import timezone
from .models import Coupon
from students.models import ProductsModel, ServicesModel
from accounts.models import StudentProfile, UserProfile

from django import forms
from django.utils import timezone
from .models import Coupon
from students.models import ProductsModel, ServicesModel
from accounts.models import StudentProfile, UserProfile


class CouponForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.coach = kwargs.pop('coach', None)
        super().__init__(*args, **kwargs)

        # Enhanced CSS classes for all fields
        field_styles = {
            'code': {
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                'placeholder': 'Enter coupon code (e.g., SAVE20)'
            },
            'description': {
                'class': 'form-textarea w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200 resize-none',
                'rows': 3,
                'placeholder': 'Enter a brief description of this coupon...'
            },
            'discount_value': {
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Enter discount value'
            },
            'max_discount': {
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Maximum discount amount'
            },
            'min_order_value': {
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Minimum order value'
            },
            'max_uses': {
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                'min': '0',
                'placeholder': 'Enter 0 for unlimited uses'
            },
            'is_active': {
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition duration-200'
            },
            'all_students': {
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition duration-200'
            },
            'apply_to_all_products': {
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition duration-200'
            },
            'apply_to_all_services': {
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition duration-200'
            },
            'selected_students': {
                'class': 'form-select select2 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                'data-placeholder': 'Select students...'
            },
            'products': {
                'class': 'form-select select2 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                'data-placeholder': 'Select products...'
            },
            'services': {
                'class': 'form-select select2 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                'data-placeholder': 'Select services...'
            }
        }

        # Apply styles to fields
        for field_name, field in self.fields.items():
            if field_name in field_styles:
                field.widget.attrs.update(field_styles[field_name])
            else:
                # Default styling for any fields not specifically styled
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs.update({
                        'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition duration-200'
                    })
                elif isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({
                        'class': 'form-select w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200'
                    })
                elif isinstance(field.widget, forms.SelectMultiple):
                    field.widget.attrs.update({
                        'class': 'form-select select2 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200'
                    })
                elif isinstance(field.widget, forms.Textarea):
                    field.widget.attrs.update({
                        'class': 'form-textarea w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200 resize-none',
                        'rows': 3
                    })
                else:
                    field.widget.attrs.update({
                        'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200'
                    })

        # Add specific attributes for date fields
        if 'start_date' in self.fields:
            self.fields['start_date'].widget.attrs.update({
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                'type': 'datetime-local'
            })

        if 'end_date' in self.fields:
            self.fields['end_date'].widget.attrs.update({
                'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                'type': 'datetime-local'
            })

        # Add specific styling for radio buttons (discount_type)
        if 'discount_type' in self.fields:
            self.fields['discount_type'].widget.attrs.update({
                'class': 'form-radio h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 transition duration-200'
            })

        # Coach-specific field filtering (your existing logic)
        if self.coach:
            try:
                user_profile = UserProfile.objects.get(Coach_profile=self.coach)
                coach_user = user_profile.user

                # Filter students from the same club as the coach
                self.fields['selected_students'].queryset = StudentProfile.objects.filter(
                    club=self.coach.club
                ).distinct()

                # Filter products and services created by this coach
                self.fields['products'].queryset = ProductsModel.objects.filter(
                    creator=coach_user
                )
                self.fields['services'].queryset = ServicesModel.objects.filter(
                    creator=coach_user
                )

            except UserProfile.DoesNotExist:
                print(f"No UserProfile found for coach: {self.coach}")
                # Set empty querysets if no UserProfile exists
                self.fields['selected_students'].queryset = StudentProfile.objects.none()
                self.fields['products'].queryset = ProductsModel.objects.none()
                self.fields['services'].queryset = ServicesModel.objects.none()
            except Exception as e:
                print(f"Error in form initialization: {e}")
                # Set empty querysets on any error
                self.fields['selected_students'].queryset = StudentProfile.objects.none()
                self.fields['products'].queryset = ProductsModel.objects.none()
                self.fields['services'].queryset = ServicesModel.objects.none()

    class Meta:
        model = Coupon
        fields = [
            'code', 'description', 'discount_type', 'discount_value', 'max_discount',
            'min_order_value', 'all_students', 'selected_students', 'apply_to_all_products',
            'apply_to_all_services', 'products', 'services', 'start_date', 'end_date',
            'is_active', 'max_uses'
        ]
        widgets = {
            'discount_type': forms.RadioSelect(
                attrs={
                    'class': 'form-radio h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 transition duration-200'}
            ),
            'start_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200'
                }
            ),
            'end_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200'
                }
            ),
            'selected_students': forms.SelectMultiple(
                attrs={
                    'class': 'form-select select2 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                    'data-placeholder': 'Select students...'
                }
            ),
            'products': forms.SelectMultiple(
                attrs={
                    'class': 'form-select select2 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                    'data-placeholder': 'Select products...'
                }
            ),
            'services': forms.SelectMultiple(
                attrs={
                    'class': 'form-select select2 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                    'data-placeholder': 'Select services...'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-textarea w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200 resize-none',
                    'rows': 3,
                    'placeholder': 'Enter a brief description of this coupon...'
                }
            ),
            'code': forms.TextInput(
                attrs={
                    'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                    'placeholder': 'Enter coupon code (e.g., SAVE20)'
                }
            ),
            'discount_value': forms.NumberInput(
                attrs={
                    'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                    'step': '0.01',
                    'min': '0',
                    'placeholder': 'Enter discount value'
                }
            ),
            'max_discount': forms.NumberInput(
                attrs={
                    'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                    'step': '0.01',
                    'min': '0',
                    'placeholder': 'Maximum discount amount'
                }
            ),
            'min_order_value': forms.NumberInput(
                attrs={
                    'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                    'step': '0.01',
                    'min': '0',
                    'placeholder': 'Minimum order value'
                }
            ),
            'max_uses': forms.NumberInput(
                attrs={
                    'class': 'form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200',
                    'min': '0',
                    'placeholder': 'Enter 0 for unlimited uses'
                }
            ),
            'is_active': forms.CheckboxInput(
                attrs={
                    'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition duration-200'
                }
            ),
            'all_students': forms.CheckboxInput(
                attrs={
                    'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition duration-200'
                }
            ),
            'apply_to_all_products': forms.CheckboxInput(
                attrs={
                    'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition duration-200'
                }
            ),
            'apply_to_all_services': forms.CheckboxInput(
                attrs={
                    'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition duration-200'
                }
            ),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code', '').upper().strip()
        if not code:
            raise forms.ValidationError("Coupon code is required")

        # Check if code already exists (excluding current instance if editing)
        existing_coupon = Coupon.objects.filter(code=code)
        if self.instance and self.instance.pk:
            existing_coupon = existing_coupon.exclude(pk=self.instance.pk)

        if existing_coupon.exists():
            raise forms.ValidationError("A coupon with this code already exists")

        return code

    def clean_discount_value(self):
        discount_value = self.cleaned_data.get('discount_value')
        if discount_value is None or discount_value <= 0:
            raise forms.ValidationError("Discount value must be greater than 0")
        return discount_value

    def clean_max_uses(self):
        max_uses = self.cleaned_data.get('max_uses')
        if max_uses is None or max_uses < 0:
            raise forms.ValidationError("Max uses must be 0 or greater")
        return max_uses

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value')

        # Validate dates
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError("End date must be after start date")

        # Validate percentage discount
        if discount_type == 'percentage' and discount_value:
            if discount_value > 100:
                raise forms.ValidationError("Percentage discount cannot exceed 100%")

        # Validate that at least one student selection is made
        all_students = cleaned_data.get('all_students')
        selected_students = cleaned_data.get('selected_students')

        if not all_students and not selected_students:
            raise forms.ValidationError("Please select either 'All Students' or choose specific students")

        # Validate that at least one product/service selection is made
        apply_to_all_products = cleaned_data.get('apply_to_all_products')
        apply_to_all_services = cleaned_data.get('apply_to_all_services')
        products = cleaned_data.get('products')
        services = cleaned_data.get('services')

        if not (apply_to_all_products or apply_to_all_services or products or services):
            raise forms.ValidationError("Please select products or services for this coupon to apply to")

        return cleaned_data


from django import forms
from .models import VendorWorkingHours
from django.utils import timezone
import datetime

class VendorWorkingHoursForm(forms.ModelForm):
    class Meta:
        model = VendorWorkingHours
        fields = [
            'title', 'start_date', 'end_date',
            'monday_open', 'monday_close',
            'tuesday_open', 'tuesday_close',
            'wednesday_open', 'wednesday_close',
            'thursday_open', 'thursday_close',
            'friday_open', 'friday_close',
            'saturday_open', 'saturday_close',
            'sunday_open', 'sunday_close',
            'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 shadow-sm transition-all duration-200',
                'placeholder': 'الجدول الصيفي 2026'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 shadow-sm transition-all duration-200'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 shadow-sm transition-all duration-200'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-5 w-5 text-blue-600 dark:text-blue-400 focus:ring-blue-500 border-gray-300 dark:border-gray-600 rounded transition duration-200'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set time inputs for all day fields
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            self.fields[f'{day}_open'].widget = forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 shadow-sm transition-all duration-200'
            })
            self.fields[f'{day}_close'].widget = forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 shadow-sm transition-all duration-200'
            })

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("End date must be after start date")

            # Don't allow schedules longer than 1 year
            if (end_date - start_date).days > 365:
                raise forms.ValidationError("Schedule cannot be longer than 1 year")

        # Validate time ranges
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            open_time = cleaned_data.get(f'{day}_open')
            close_time = cleaned_data.get(f'{day}_close')

            if open_time and close_time:
                if close_time <= open_time:
                    raise forms.ValidationError(f"{day.capitalize()} closing time must be after opening time")

        return cleaned_data

    def get_days_fields(self):
        days = [
            {'name': 'monday', 'label': 'Monday'},
            {'name': 'tuesday', 'label': 'Tuesday'},
            {'name': 'wednesday', 'label': 'Wednesday'},
            {'name': 'thursday', 'label': 'Thursday'},
            {'name': 'friday', 'label': 'Friday'},
            {'name': 'saturday', 'label': 'Saturday'},
            {'name': 'sunday', 'label': 'Sunday'},
        ]

        for day in days:
            day['open_field'] = self[f'{day["name"]}_open']
            day['close_field'] = self[f'{day["name"]}_close']

        return days