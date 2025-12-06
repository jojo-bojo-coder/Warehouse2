from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views  # ✅ Import views properly
from .views import mark_notifications_read  # ✅ Import the view
from .views import viewClubNotifications  # ✅ Import the view function
from django.utils import translation
from django.shortcuts import redirect
import administrator_dashboard.views as administrator_views

def set_language_redirect(request, language):
    translation.activate(language)
    response = redirect(request.GET.get('next', '/'))
    response.set_cookie('django_language', language)
    return response

# ✅ Import necessary views once
from .views import (
    viewDirectors, addDirector, editDirector, deleteDirector
)

urlpatterns = [
    path('', views.club_dashboard_index, name="club_dashboard_index"),
    path('club/landing/edit/', views.edit_landing_content, name='edit_landing_content'),

    # Features management
    path('club/landing/features/', views.manage_features, name='manage_features'),
    path('club/landing/features/<int:feature_id>/edit/', views.edit_feature, name='edit_feature'),
    path('club/landing/features/<int:feature_id>/delete/', views.delete_feature, name='delete_feature'),

    # Banners management
    path('club/landing/banners/', views.manage_banners, name='manage_banners'),
    path('club/landing/banners/<int:banner_id>/delete/', views.delete_banner, name='delete_banner'),

    # FAQs management
    path('club/landing/faqs/', views.manage_faqs, name='manage_faqs'),
    path('club/landing/faqs/<int:faq_id>/delete/', views.delete_faq, name='delete_faq'),

    # Navigation items management
    path('club/landing/nav-items/', views.manage_nav_items, name='manage_nav_items'),
    path('club/<int:club_id>/contact/update/', views.update_club_contact, name='update_club_contact'),
    path('club/landing/nav-items/<int:nav_item_id>/delete/', views.delete_nav_item, name='delete_nav_item'),
    path('set-language/<str:language>/', set_language_redirect, name='set_language_redirect'),
    # Students Management
    path('viewStudents', views.viewStudents, name="viewStudents"),
    path('export-students-excel/', views.export_students_excel, name='export_students_excel'),
    path('addStudent', views.addStudent, name="addStudent"),
    path('students/add/confirm-duplicate/', views.confirm_student_duplicate, name='confirm_student_duplicate'),
    path('editStudent/<int:id>', views.editStudent, name="editStudent"),
    path('deleteStudent/<int:id>', views.deleteStudent, name="deleteStudent"),
    path('students/import/', views.import_students, name='import_students'),
    path('students/process-import/', views.process_import_students, name='process_import_students'),
    path('students/download-template/', views.download_sample_template, name='download_sample_template'),

    # Coaches Management
    path('viewCoachs', views.viewCoachs, name="viewCoachs"),
    path('export_coaches_excel/', views.export_coaches_excel, name='export_coaches_excel'),
    path('addCoach', views.addCoach, name="addCoach"),
    path('editCoach/<int:id>', views.editCoach, name="editCoach"),    
    path('deleteCoach/<int:id>', views.deleteCoach, name="deleteCoach"),
    # New Vendor URLs
    path('vendor-status/<int:vendor_id>/', views.vendor_status, name='vendor_status'),
    path('vendor-approval/', views.vendor_approval_list, name='vendor_approval_list'),
    path('vendor-approval/action/<int:vendor_id>/', views.vendor_approval_action, name='vendor_approval_action'),
    path('vendor-approval/<int:vendor_id>/', views.vendor_approval_detail, name='vendor_approval_detail'),
    path('vendors/pending/<int:pk>/', views.VendorApprovalDetailView.as_view(), name='vendor_approval_detail'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('pending-products/', views.pending_products, name='pending_products'),

    # Services Management
    path('delete-service/<int:service_id>/', views.delete_service, name='delete_service'),
    path('services/pending/', views.pending_services, name='pending_services'),


    # Service Management URLs
    path('services/manage/', views.manage_services, name='manage_services'),
    path('services/<int:service_id>/approve/', views.approve_service, name='approve_service'),
    path('services/<int:service_id>/reject/', views.reject_service, name='reject_service'),
    path('services/<int:service_id>/detail/', views.service_detail, name='service_detail'),
    path('services/<int:service_id>/toggle-status/', views.toggle_service_status, name='toggle_service_status'),
    path('services/bulk-approve/', views.bulk_approve_services, name='bulk_approve_services'),
    path('services/bulk-reject/', views.bulk_reject_services, name='bulk_reject_services'),

    # Blog Management
    path('articles/', views.viewArticles, name="viewArticles"),
    path('articles/add/', views.addArticle, name="addArticle"),
    path('articles/edit/<int:id>/', views.editArticle, name="editArticle"),
    path('articles/delete/<int:id>/', views.DeleteArticle, name="DeleteArticle"),
    path('viewDirectors/', viewDirectors, name="viewDirectors"),  # ✅ This now matches your working URL
    path('viewDirectors/add/', addDirector, name="addDirector"),
    path('edit-director/<int:id>/<str:role>/', views.editDirector, name='editDirector'),
    path('delete-director/<int:id>/<str:role>/', views.deleteDirector, name='deleteDirector'),
    path('mark-notifications-read/', mark_notifications_read, name='mark_notifications_read'),
    path('notifications/', viewClubNotifications, name='viewClubNotifications'),  # ✅ Ensure correct name
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('notifications/delete-all/', views.delete_all_notifications, name='delete_all_notifications'),
    path('reviews/', views.reviews_list, name='reviews_list'),
    path('delete-review/<int:review_id>/', views.delete_review, name='delete_review'),

    # ✅ Correct URL
    path('club/orders/', views.club_orders, name='club_orders'),
    path('club/orders/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
    path('club/orders/<int:order_id>/details/', views.order_details_api, name='order_details_api'),
    path('club/orders/<int:order_id>/full-details/', views.order_full_details, name='order_full_details'),
    path('orders/cancellation/<int:order_id>/', views.get_cancellation_details, name='get_cancellation_details'),
    path('financial-dashboard/', views.club_financial_dashboard, name='club_financial_dashboard'),
    path('financial/export/', views.export_financial_data, name='export_financial_data'),
    path('profile/director/', views.view_director_profile, name='view_director_profile'),
    path('profile/director/edit/', views.edit_director_profile, name='edit_director_profile'),
    path('profile/administrator/', administrator_views.view_administrator_profile, name='view_administrator_profile'),
    path('profile/administrator/edit/', administrator_views.edit_administrator_profile, name='edit_administrator_profile'),
    path('toggle-dashboard-counts/', views.toggle_dashboard_counts, name='toggle_dashboard_counts'),
    path('club/update-descriptions/<int:club_id>/', views.update_club_descriptions, name='UpdateClubDescriptions'),
    path('mark-notifications-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('add-role/', views.add_custom_role, name='add_custom_role'),
    path('custom-roles/', views.view_custom_roles, name='view_custom_roles'),
    path('custom-roles/edit/<int:id>/', views.edit_custom_role, name='edit_custom_role'),
    path('custom-roles/delete/<int:id>/', views.delete_custom_role, name='delete_custom_role'),

    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('categories/<int:category_id>/detail/', views.category_detail, name='category_detail'),

    # Subcategory URLs
    path('subcategories/add/', views.add_subcategory, name='add_subcategory'),
    path('subcategories/<int:subcategory_id>/edit/', views.edit_subcategory, name='edit_subcategory'),
    path('subcategories/<int:subcategory_id>/delete/', views.delete_subcategory, name='delete_subcategory'),

    # AJAX URLs
    path('categories/<int:category_id>/subcategories/', views.get_subcategories, name='get_subcategories'),
    path('categories/<int:category_id>/toggle-status/', views.toggle_category_status, name='toggle_category_status'),
    path('subcategories/<int:subcategory_id>/toggle-status/', views.toggle_subcategory_status, name='toggle_subcategory_status'),

    # Product management URLs
    path('manage-products/', views.manage_products, name='manage_products'),
    path('approve-product/<int:product_id>/', views.approve_product, name='approve_product'),
    path('reject-product/<int:product_id>/', views.reject_product, name='reject_product'),
    path('product-detail/<int:product_id>/', views.product_detail, name='product_detail'),
    path('bulk-approve-products/', views.bulk_approve_products, name='bulk_approve_products'),
    path('bulk-reject-products/', views.bulk_reject_products, name='bulk_reject_products'),

    # Commission management URLs
    path('commissions/', views.commission_list, name='commission_list'),
    path('commissions/create/', views.commission_create, name='commission_create'),
    path('commissions/<int:commission_id>/edit/', views.commission_edit, name='commission_edit'),
    path('commissions/<int:commission_id>/toggle-status/', views.commission_toggle_status, name='commission_toggle_status'),
    path('commissions/<int:commission_id>/detail/', views.commission_detail, name='commission_detail'),
    path('commissions/vendor-management/', views.vendor_commission_management, name='vendor_commission_management'),
    path('commissions/analytics/', views.commission_analytics, name='commission_analytics'),
    path('commissions/<int:commission_id>/delete/', views.delete_commission, name='delete_commission'),


    # Dashboard and main views
    path('refund_dashboard/', views.refund_dashboard, name='dashboard'),
    path('dispute/<int:dispute_id>/', views.refund_detail, name='detail'),

    # Actions
    path('dispute/<int:dispute_id>/approve/', views.approve_refund, name='approve'),
    path('dispute/<int:dispute_id>/reject/', views.reject_refund, name='reject'),
    path('dispute/<int:dispute_id>/investigate/', views.mark_investigating, name='investigate'),
    path('dispute/<int:dispute_id>/resolve/', views.resolve_dispute, name='resolve'),
    path('dispute/<int:dispute_id>/priority/', views.update_dispute_priority, name='update_priority'),

    # Bulk actions
    path('bulk-action/', views.bulk_action, name='bulk_action'),

    # Export
    path('export/', views.export_disputes, name='export'),

    # API endpoints
    path('api/stats/', views.get_dispute_stats, name='api_stats'),
    path('coach/<int:coach_id>/', views.coach_details, name='coach_details'),

    path('director/promotions/', views.director_promotions, name='director_promotions'),
    path('director/approve-promotion/<int:promotion_id>/', views.approve_promotion, name='approve_promotion'),
    path('director/reject-promotion/<int:promotion_id>/', views.reject_promotion, name='reject_promotion'),
    path('view-promotion/<int:promotion_id>/', views.view_pending_promotion, name='view_pending_promotion'),
    # Feature Management URLs
    path('promotions/features/', views.manage_promotion_features, name='manage_promotion_features'),
    path('promotions/features/save/', views.save_promotion_feature, name='save_promotion_feature'),
    path('promotions/features/delete/<int:feature_id>/', views.delete_promotion_feature,
         name='delete_promotion_feature'),
    path('promotions/features/set-base-price/', views.set_promotion_base_price, name='set_promotion_base_price'),
    path('director/bills/', views.director_bills_review, name='director_bills_review'),
    path('director/bills/review/<int:revision_id>/', views.director_review_bill, name='director_review_bill'),

    path('director/vat-settings/', views.manage_vat_settings, name='manage_vat_settings'),

]

# ✅ Ensure media files work in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
