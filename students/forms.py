from django import forms
from students.models import Review

from django import forms
from students.models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        # Accept order_item as a parameter to determine product/service
        self.order_item = kwargs.pop('order_item', None)
        super().__init__(*args, **kwargs)

        # Pre-populate the instance with product or service if it's a new review
        if self.order_item and not self.instance.pk:
            if self.order_item.product:
                self.instance.product = self.order_item.product
            elif self.order_item.service:
                self.instance.service = self.order_item.service

    def clean(self):
        cleaned_data = super().clean()

        # Ensure product or service is set for validation
        if self.order_item and self.instance:
            if self.order_item.product and not self.instance.product:
                self.instance.product = self.order_item.product
            elif self.order_item.service and not self.instance.service:
                self.instance.service = self.order_item.service

        return cleaned_data

    def save(self, commit=True):
        review = super().save(commit=False)

        # Ensure product or service is set (should already be set in __init__)
        if self.order_item:
            if self.order_item.product and not review.product:
                review.product = self.order_item.product
            elif self.order_item.service and not review.service:
                review.service = self.order_item.service

        if commit:
            review.save()
        return review




from django import forms
from club_dashboard.models import RefundDispute, RefundDisputeAttachment
from .widgets import MultipleFileInput
from django.core.files.uploadedfile import UploadedFile


from django import forms
from club_dashboard.models import RefundDispute, RefundDisputeAttachment
from .widgets import MultipleFileInput
from django.core.files.uploadedfile import UploadedFile


class RefundDisputeForm(forms.ModelForm):
    attachments = forms.FileField(
        widget=MultipleFileInput(attrs={'accept': 'image/*, .pdf, .doc, .docx, .txt, video/*'}),
        required=False,
        label="Attachments"
    )
    attachment_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Attachment Description"
    )

    class Meta:
        model = RefundDispute
        fields = ['title', 'description', 'dispute_type',
                  'priority', 'refund_type', 'requested_refund_amount']
        # Removed 'deal' from fields since we'll handle it automatically

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.order_item = kwargs.pop('order_item', None)  # Add order_item parameter
        super().__init__(*args, **kwargs)

        # Remove the deal field since we'll handle it automatically
        if 'deal' in self.fields:
            del self.fields['deal']

        # Set initial requested refund amount to the item's price
        if self.order_item:
            self.fields['requested_refund_amount'].initial = self.order_item.price * self.order_item.quantity

    def clean(self):
        cleaned_data = super().clean()

        # Validate that requested refund amount doesn't exceed item amount
        requested_amount = cleaned_data.get('requested_refund_amount')
        if self.order_item and requested_amount:
            max_amount = self.order_item.price * self.order_item.quantity
            if requested_amount > max_amount:
                raise forms.ValidationError({
                    'requested_refund_amount': 'Requested refund cannot exceed the original item amount.'
                })

        return cleaned_data

    def save(self, commit=True):
        dispute = super().save(commit=False)

        # Set the client to the current user
        if self.user:
            dispute.client = self.user

        # Set the deal and order item from the provided order_item
        if self.order_item:
            dispute.deal = self.order_item.order
            dispute.order_item = self.order_item
            dispute.original_amount = self.order_item.price * self.order_item.quantity

            # Set vendor based on product/service
            if hasattr(self.order_item, 'product') and self.order_item.product:
                dispute.vendor = self.order_item.product.creator
            elif hasattr(self.order_item, 'service') and self.order_item.service:
                dispute.vendor = self.order_item.service.creator

        if commit:
            dispute.save()
            # Save attachments after the dispute is saved
            self.save_attachments(dispute)

        return dispute

    def save_attachments(self, dispute):
        """Save uploaded attachments"""
        if 'attachments' in self.files:
            files = self.files.getlist('attachments')
            description = self.cleaned_data.get('attachment_description', '')

            for file in files:
                file_type = self.determine_file_type(file)
                RefundDisputeAttachment.objects.create(
                    refund_dispute=dispute,
                    file=file,
                    description=description,
                    uploaded_by=self.user,
                    file_type=file_type
                )

    def determine_file_type(self, file: UploadedFile) -> str:
        """Determine file type based on content type and extension"""
        if not isinstance(file, UploadedFile):
            return 'other'

        # Check content type first
        if hasattr(file, 'content_type') and file.content_type:
            content_type = file.content_type.split('/')[0]
            if content_type == 'image':
                return 'image'
            elif content_type == 'video':
                return 'video'

        # Check file extension
        if hasattr(file, 'name') and file.name:
            if file.name.lower().endswith(('.pdf', '.doc', '.docx', '.txt')):
                return 'document'
            elif file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                return 'image'
            elif file.name.lower().endswith(('.mp4', '.avi', '.mov', '.wmv')):
                return 'video'

        return 'other'
