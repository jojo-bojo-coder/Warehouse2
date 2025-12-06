from accounts.models import CoachProfile, DirectorProfile, StudentProfile, ClubsModel
from django import forms

# class CoachProfileModelForm(forms.ModelForm):
#
#     class Meta:
#         model = CoachProfile
#         fields = ['full_name', 'phone', 'major', 'about']
#
#         widgets = {
#         'full_name': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
#         'phone': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
#         # 'stadium': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
#         'major': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
#         'about': forms.Textarea(attrs={'rows':'5', 'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
#
#         }

class StudentProfileModelForm(forms.ModelForm):

    class Meta:
        model = StudentProfile
        fields = ['full_name', 'phone', 'birthday', 'about']

        widgets = {
        'full_name': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
        'phone': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
        'birthday': forms.TextInput(attrs={'type':'date', 'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
        'about': forms.Textarea(attrs={'rows':'5', 'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
        }


class DirectorProfileModelForm(forms.ModelForm):

    class Meta:
        model = DirectorProfile
        fields = ['full_name', 'phone', 'about']

        widgets = {
        'full_name': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
        'phone': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
        'about': forms.Textarea(attrs={'rows':'5', 'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
        }

class ClubsModelForm(forms.ModelForm):
    club_profile_image_base64 = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'})
    )

    class Meta:
        model = ClubsModel
        fields = ['name', 'desc', 'about', 'city', 'district', 'street', 'club_profile_image_base64']  # Include image field

        widgets = {
            'name': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
            'desc': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
            'city': forms.Select(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
            'district': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
            'street': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
            'about': forms.Textarea(attrs={'rows':'5', 'class':'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'}),
        }

from .models import ClubSecuritySettings
class ClubSecuritySettingsForm(forms.ModelForm):
    class Meta:
        model = ClubSecuritySettings
        fields = [
            'enable_otp_verification',
            'enable_recaptcha',
            'otp_method',
            'otp_expiry_minutes'
        ]
        widgets = {
            'enable_otp_verification': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 rounded focus:ring-blue-500',
                'id': 'enable_otp'
            }),
            'enable_recaptcha': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 rounded focus:ring-blue-500',
                'id': 'enable_recaptcha'
            }),
            'otp_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'id': 'otp_method'
            }),
            'otp_expiry_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'min': 1,
                'max': 60
            }),
        }
        labels = {
            'enable_otp_verification': 'تفعيل التحقق بخطوتين (OTP)',
            'enable_recaptcha': 'تفعيل reCAPTCHA في صفحة تسجيل الدخول',
            'otp_method': 'طريقة إرسال رمز التحقق',
            'otp_expiry_minutes': 'مدة صلاحية رمز التحقق (دقائق)'
        }