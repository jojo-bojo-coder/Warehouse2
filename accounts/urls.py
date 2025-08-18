from django.urls import path
from . import views
from django.utils import translation
from django.shortcuts import redirect
from django.conf import settings

def set_language_redirect(request, language):
    translation.activate(language)
    response = redirect(request.GET.get('next', '/'))
    response.set_cookie('django_language', language)
    return response

urlpatterns = [
    path('signin/', views.signin, name='signin'),
    path('select-otp-method/', views.select_otp_method, name='select_otp_method'),
    path('send-otp-whatsapp/', views.send_otp_whatsapp, name='send_otp_whatsapp'),
    path('send-otp-email/', views.send_otp_email, name='send_otp_email'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('signup', views.signup, name='signup'),
    path('subscription-info/', views.subscription_info, name='subscription_info'),
    path('director-pricing/', views.director_pricing, name='director_pricing'),
    path('select-plan/<int:plan_id>/', views.select_pricing_plan, name='select_pricing_plan'),
    # Payment flow
    path('director-checkout/<int:plan_id>/', views.director_checkout, name='director_checkout'),
    path('director-verify-otp/', views.director_verify_otp, name='director_verify_otp'),
    path('complete-director-signup/', views.complete_director_signup_after_payment, name='complete_director_signup'),
    path('signout', views.signout, name='signout'),
    path('set-language/<str:language>/', set_language_redirect, name='set_language_redirect'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('select-subcategories/', views.select_subcategories, name='select_subcategories'),
    path('api/cities/', views.get_cities_by_region, name='get_cities_by_region'),
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),

]
