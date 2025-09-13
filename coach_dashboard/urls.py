from django.urls import path
from . import views
from django.utils import translation
from django.shortcuts import redirect

def set_language_redirect(request, language):
    translation.activate(language)
    response = redirect(request.GET.get('next', '/'))
    response.set_cookie('django_language', language)
    return response

urlpatterns = [

    path('', views.index, name="coachIndex"),
    path('set-language/<str:language>/', set_language_redirect, name='set_language_redirect'),
    path('vendorProfile', views.view_coach_profile, name="coachVendorProfile"),
    path('editProfile', views.edit_coach_profile, name="editCoachProfile"),
    # Products Management
    path('addProduct', views.addProduct, name="coachaddProduct"),
    path('editProduct/<int:id>', views.editProduct, name="coacheditProduct"),
    path('DeleteProduct/<int:id>', views.DeleteProduct, name="coachDeleteProduct"),
    path('viewProducts', views.viewProducts, name="coachviewProducts"),
    path('products/shipments/add/', views.add_shipment, name='coachadd_shipment'),
    path('products/<int:product_id>/shipments/', views.view_product_shipments, name='coachview_product_shipments'),
    path('shipments/edit/<int:shipment_id>/', views.edit_shipment, name='coachedit_shipment'),
    path('shipments/delete/<int:shipment_id>/', views.delete_shipment, name='coachdelete_shipment'),
    path('products/<int:product_id>/details/', views.product_details, name='coachproduct_details'),

    # Services Management
    path('addServices', views.addServices, name="coachaddServices"),
    path('editServices/<int:id>', views.editServices, name="coacheditServices"),
    path('DeleteServices/<int:id>', views.DeleteServices, name="coachDeleteServices"),
    path('viewServices', views.viewServices, name="coachviewServices"),
    path('services/details/<int:service_id>/', views.viewServiceDetails, name='coachviewServiceDetails'),

    path('addServicesClassification', views.addServicesClassification, name="coachaddServicesClassification"),
    path('editServicesClassification/<int:id>', views.editServicesClassification, name="coacheditServicesClassification"),
    path('DeleteServicesClassification/<int:id>', views.DeleteServicesClassification, name="coachDeleteServicesClassification"),
    path('viewServicesClassification', views.viewServicesClassification, name="coachviewServicesClassification"),
    path('notifications/', views.viewCoachNotifications , name='viewCoachNotifications'),  # ✅ Ensure correct name
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='coach_delete_notification'),
    path('notifications/delete-all/', views.delete_all_notifications, name='coach_delete_all_notifications'),

    path('orders/', views.viewOrders, name='coachviewOrders'),
    path('orders/<int:order_id>/', views.viewOrderDetails, name='coachviewOrderDetails'),
    path('business-profile/', views.view_business_profile, name='view_business_profile'),
    path('business-profile/edit/', views.edit_business_profile, name='edit_business_profile'),
    path('reviews/', views.coach_reviews, name='coach_reviews'),
    path('reviews/<str:item_type>/<int:item_id>/', views.product_service_reviews, name='product_service_reviews'),
    path('upload-policies/', views.upload_policies, name='upload_policies'),
    path('view-policies/', views.view_policies, name='view_policies'),
    path('edit-policies/', views.edit_policies, name='edit_policies'),
    path('coach/tickets/', views.coach_ticket_list, name='coach_ticket_list'),
    path('coach/tickets/new/', views.create_coach_ticket, name='create_coach_ticket'),
    path('coach/tickets/<int:ticket_id>/', views.coach_ticket_detail, name='coach_ticket_detail'),
    path('coach/refunds/', views.coach_refund_requests, name='coach_refund_requests'),
    path('coach/refunds/<int:dispute_id>/', views.coach_refund_detail, name='coach_refund_detail'),
    path('orders/<int:order_id>/update_status/', views.update_order_status, name='update_order_status'),
    path('financials/', views.coach_financials, name='coach_financials'),
    path('students/', views.coach_students, name='coach_students'),
    path('receptionist/set-status/', views.set_receptionist_status, name='set_receptionist_status'),
    path('receptionist/claim-ticket/', views.assign_pending_tickets, name='assign_pending_tickets'),
    path('edit-bank-info/', views.edit_bank_info, name='edit_bank_info'),
    path('working-hours/', views.working_hours, name='working_hours'),
    path('coach-performance/', views.coach_performance, name='coach_performance'),
    path('payments/', views.coach_payments, name='coach_payments'),
    path('coach/marketing/', views.coach_marketing_dashboard, name='coach_marketing'),
    path('marketing/create-promotion/', views.create_promotion, name='create_promotion'),
    path('marketing/get-price/', views.get_promotion_price, name='get_promotion_price'),

    path('coupons/', views.coach_coupons, name='coach_coupons'),
    path('coupons/add/', views.add_coupon, name='add_coupon'),
    path('coupons/edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('coupons/toggle/<int:coupon_id>/', views.toggle_coupon_status, name='toggle_coupon_status'),
    path('coupons/delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),
    path('coupons/usage/<int:coupon_id>/', views.coupon_usage, name='coupon_usage'),
    path('vendor-working-hours/', views.vendor_working_hours_list, name='vendor_working_hours_list'),
    path('vendor-working-hours/add/', views.add_vendor_working_hours, name='add_vendor_working_hours'),
    path('vendor-working-hours/edit/<int:pk>/', views.edit_vendor_working_hours, name='edit_vendor_working_hours'),
    path('vendor-working-hours/toggle/<int:pk>/', views.toggle_vendor_working_hours, name='toggle_vendor_working_hours'),
    path('vendor-working-hours/delete/<int:pk>/', views.delete_vendor_working_hours, name='delete_vendor_working_hours'),


]
