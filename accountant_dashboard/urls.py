from accountant_dashboard import views as accountant_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.utils import translation
from django.shortcuts import redirect

def set_language_redirect(request, language):
    translation.activate(language)
    response = redirect(request.GET.get('next', '/'))
    response.set_cookie('django_language', language)
    return response

urlpatterns = [
    path('set-language/<str:language>/', set_language_redirect, name='set_language_redirect'),
    path('accountant/', accountant_views.accountant_dashboard, name='accountant_dashboard'),
    path('accountant/revenue-analytics/', accountant_views.revenue_analytics, name='accountant_revenue_analytics'),
    path('accountant/vat-settings/', accountant_views.vat_settings, name='accountant_vat_settings'),
    path('bills/', accountant_views.accountant_bills_review, name='accountant_bills_review'),
    path('bills/review/<int:order_id>/', accountant_views.accountant_review_bill, name='accountant_review_bill'),
    path('custom-financial-reports/', accountant_views.custom_financial_reports, name='accountant_custom_financial_reports'),
    path('banners/', accountant_views.banner_management, name='accountant_banner_management'),
    path('banners/add/', accountant_views.add_banner, name='accountant_add_banner'),
    path('banners/edit/<int:banner_id>/', accountant_views.edit_banner, name='accountant_edit_banner'),
    path('banners/delete/<int:banner_id>/', accountant_views.delete_banner, name='accountant_delete_banner'),
    path('marketing-reports/', accountant_views.marketing_analysis_reports, name='accountant_marketing_reports'),
    path('expense-analytics/', accountant_views.expense_analytics, name='accountant_expense_analytics'),
    path('cms-settings/', accountant_views.cms_settings, name='accountant_cms_settings'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)