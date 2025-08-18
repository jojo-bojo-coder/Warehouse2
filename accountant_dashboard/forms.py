from django import forms
from .models import VATSettings


class VATSettingsForm(forms.ModelForm):
    LANGUAGE_CHOICES = [
        ('ar', 'العربية'),
        ('en', 'English'),
    ]

    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'block w-full px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out',
        }),
        label="Language"
    )

    class Meta:
        model = VATSettings
        fields = [ 'currency', 'language']
        widgets = {
            'currency': forms.Select(attrs={
                'class': 'block w-full px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out',
            })
        }

    def __init__(self, *args, **kwargs):
        initial_language = kwargs.pop('language', None)
        super().__init__(*args, **kwargs)
        if initial_language:
            self.initial['language'] = initial_language

    def clean(self):
        cleaned_data = super().clean()

        return cleaned_data


from django import forms
from .models import BillRevision, BillRevisionComment


class BillRevisionForm(forms.ModelForm):
    accountant_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'أدخل ملاحظاتك حول هذه الفاتورة...'
        }),
        required=False
    )

    class Meta:
        model = BillRevision
        fields = ['accountant_notes']


class BillRevisionCommentForm(forms.ModelForm):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 2,
            'placeholder': 'اضف تعليق...'
        }),
        required=True
    )

    class Meta:
        model = BillRevisionComment
        fields = ['comment']




from django import forms
from .models import Banner

class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['title', 'image', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ',
                'placeholder': 'أدخل عنوان للبانر'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700 dark:text-gray-300'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }







from .models import LandingPageContent, TermsAndConditions

class LandingPageContentForm(forms.ModelForm):
    class Meta:
        model = LandingPageContent
        exclude = ['club']
        widgets = {
            'hero_title': forms.TextInput(attrs={'class': 'form-control'}),
            'hero_subtitle': forms.TextInput(attrs={'class': 'form-control'}),
            'about_title': forms.TextInput(attrs={'class': 'form-control'}),
            'about_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'features_title': forms.TextInput(attrs={'class': 'form-control'}),
            'plans_title': forms.TextInput(attrs={'class': 'form-control'}),
            'cta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'cta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TermsAndConditionsForm(forms.ModelForm):
    class Meta:
        model = TermsAndConditions
        exclude = ['club']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 20}),
        }