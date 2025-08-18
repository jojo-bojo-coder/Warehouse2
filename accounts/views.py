import random
from django.utils.timezone import now,timedelta
import base64
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages  # Import Django messages framework
from .forms import StudentProfileForm, DirectorSignupForm , ReceptionistSignupForm,AdministratorSignupForm,ForgotPasswordForm,ResetPasswordForm,VendorRegistrationForm,VendorApprovalForm
from .models import UserProfile, DirectorProfile, ClubsModel,ReceptionistProfile, CoachProfile,StudentProfile,OTP,PasswordResetToken,Subscription
from django.utils import translation
import string
from django.core.exceptions import ValidationError
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from django.utils import translation
from django.contrib import messages
from django.http import JsonResponse
import random
import string
from datetime import datetime, timedelta
import time
import threading


def get_main_club():
    """Get the main club instance"""
    try:
        return ClubsModel.objects.get(id=settings.MAIN_CLUB_ID)
    except ClubsModel.DoesNotExist:
        # Fallback to first club if main club doesn't exist
        return ClubsModel.objects.first()


def generate_otp():
    return str(random.randint(100000, 999999))


def send_email_otp(email, otp_code, user_name):
    """Send OTP via email"""
    try:
        subject = "رمز التحقق - المنصة"

        message = f"""
        مرحباً {user_name},

        رمز التحقق الخاص بك هو: {otp_code}

        هذا الرمز صالح لمدة 5 دقائق فقط.
        لا تشارك هذا الرمز مع أي شخص.

        شكراً لك
        فريق المنصة
        """

        send_mail(
            subject,
            message,
            "noreply@yourdomain.com",
            [email],
            fail_silently=False,
        )
        return True, "تم إرسال رمز التحقق عبر البريد الإلكتروني بنجاح"

    except Exception as e:
        return False, f"خطأ في إرسال البريد الإلكتروني: {str(e)}"


import requests
from django.conf import settings
def signin(request):
    """Step 1: Verify email/username & password, then choose OTP method"""

    context = {}
    if request.method == 'POST':
        recaptcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()

        if not result.get('success'):
            return render(request, 'accounts/sign/signin.html',
                          {"error": "الرجاء إكمال التحقق من reCAPTCHA."})


        email_or_username = request.POST.get('email').strip().lower()
        password = request.POST.get('password')

        # Try to find user by email first, then by username
        user = User.objects.filter(email=email_or_username).first()
        if not user:
            user = User.objects.filter(username=email_or_username).first()

        if user:
            user = authenticate(username=user.username, password=password)
            if user:
                # Check if user is admin (account_type '1') - skip OTP for admin
                try:
                    if user.userprofile.account_type == '1':
                        login(request, user)
                        return redirect('adminIndex')
                    elif user.userprofile.account_type == '2':
                        login(request, user)
                        return redirect('club_dashboard_index')
                    elif user.userprofile.account_type == '4':
                        login(request, user)
                        return redirect('coachIndex')
                    elif user.userprofile.account_type == '7':
                        login(request, user)
                        return redirect('accountant_dashboard')
                    elif user.userprofile.account_type == '5':
                        login(request, user)
                        return redirect('receptionistIndex')
                    elif user.userprofile.account_type == '3':
                        login(request, user)
                        return redirect('studentIndex')
                except UserProfile.DoesNotExist:
                    pass
            if user:
                try:
                    user_profile = UserProfile.objects.get(user=user)

                    # Check if user has phone number for WhatsApp option
                    phone_number = None
                    if hasattr(user_profile, 'student_profile') and user_profile.student_profile:
                        phone_number = user_profile.student_profile.phone
                    elif hasattr(user_profile, 'director_profile') and user_profile.director_profile:
                        phone_number = user_profile.director_profile.phone
                    elif hasattr(user_profile, 'Coach_profile') and user_profile.Coach_profile:
                        coach_profile = user_profile.Coach_profile
                        phone_number = coach_profile.phone
                        activity_name = coach_profile.activity_type.name if coach_profile.activity_type else "غير محدد"
                    elif hasattr(user_profile, 'receptionist_profile') and user_profile.receptionist_profile:
                        phone_number = user_profile.receptionist_profile.phone
                    elif hasattr(user_profile, 'administrator_profile') and user_profile.administrator_profile:
                        phone_number = user_profile.administrator_profile.phone
                    elif hasattr(user_profile, 'accountant_profile') and user_profile.accountant_profile:
                        phone_number = user_profile.accountant_profile.phone
                    # Add other profile types as needed



                    # Store user info in session for OTP method selection
                    request.session['otp_user_id'] = user.id
                    request.session['user_phone'] = phone_number
                    request.session['user_email'] = user.email
                    request.session['user_name'] = user.get_full_name() or user.username

                    # If user has phone number, show OTP method selection
                    if phone_number:
                        return redirect('select_otp_method')
                    else:
                        # No phone number, send OTP via email directly
                        return redirect('send_otp_email')

                except UserProfile.DoesNotExist:
                    return render(request, 'accounts/sign/signin.html',
                                  {"error": "ملف المستخدم غير موجود."})

        return render(request, 'accounts/sign/signin.html',
                      {"error": "البريد الإلكتروني أو كلمة المرور غير صحيحة."})

    context['LANGUAGE_CODE'] = translation.get_language()
    context['RECAPTCHA_PUBLIC_KEY'] = settings.RECAPTCHA_PUBLIC_KEY
    return render(request, 'accounts/sign/signin.html', context)


def select_otp_method(request):
    """Step 2: Let user choose OTP delivery method"""

    if 'otp_user_id' not in request.session:
        return redirect('signin')

    context = {
        'LANGUAGE_CODE': translation.get_language(),
        'user_phone': request.session.get('user_phone'),
        'user_email': request.session.get('user_email'),
    }

    if request.method == 'POST':
        method = request.POST.get('otp_method')

        if method == 'whatsapp':
            return redirect('send_otp_email')
        elif method == 'email':
            return redirect('send_otp_email')

    return render(request, 'accounts/sign/select_otp_method.html', context)



def send_otp_email(request):
    """Step 3b: Send OTP via Email"""

    if 'otp_user_id' not in request.session:
        return redirect('signin')

    try:
        user_id = request.session['otp_user_id']
        user = User.objects.get(id=user_id)
        email = request.session.get('user_email')
        user_name = request.session.get('user_name')

        # Generate and save OTP
        otp_code = generate_otp()
        OTP.objects.update_or_create(
            user=user,
            defaults={
                "otp_code": otp_code,
                "created_at": timezone.now(),
                "delivery_method": "email"
            }
        )

        # Send email
        success, message = send_email_otp(email, otp_code, user_name)

        if success:
            messages.success(request, "تم إرسال رمز التحقق عبر البريد الإلكتروني.")
            return redirect('verify_otp')
        else:
            messages.error(request, message)
            return redirect('select_otp_method')

    except Exception as e:
        messages.error(request, f"خطأ في إرسال رمز التحقق: {str(e)}")
        return redirect('select_otp_method')



from django.db import IntegrityError


def verify_otp(request):
    """Step 4: Verify OTP code"""

    if 'otp_user_id' not in request.session:
        return redirect('signin')

    context = {
        'LANGUAGE_CODE': translation.get_language()
    }

    if request.method == 'POST':
        otp_input = request.POST.get('otp').strip()
        user_id = request.session.get('otp_user_id')

        try:
            user = User.objects.get(id=user_id)
            otp_record = OTP.objects.filter(user=user).first()

            if not otp_record:
                context['error'] = "رمز التحقق غير موجود. يرجى إعادة المحاولة."
                return render(request, 'accounts/sign/otp_verify.html', context)

            # Check if OTP is expired (5 minutes)
            if timezone.now() - otp_record.created_at > timedelta(minutes=5):
                context['error'] = "رمز التحقق منتهي الصلاحية. يرجى إعادة المحاولة."
                return render(request, 'accounts/sign/otp_verify.html', context)

            # Verify OTP
            if otp_record.otp_code == otp_input:
                # Login user
                login(request, user)

                # Clean up
                otp_record.delete()
                for key in ['otp_user_id', 'user_phone', 'user_email', 'user_name']:
                    request.session.pop(key, None)

                # Redirect based on user type
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    account_type = user_profile.account_type

                    if account_type == '4':
                        coach_profile = user_profile.Coach_profile
                        if coach_profile and not coach_profile.subcategories.exists():
                            return redirect('select_subcategories')
                        return redirect('coachIndex')

                    if account_type == '1':  # admin
                        return redirect('adminIndex')
                    elif account_type == '2':  # director
                        return redirect('club_dashboard_index')
                    elif account_type == '3':  # student
                        return redirect('studentIndex')
                    elif account_type == '4':  # coach
                        return redirect('coachIndex')
                    elif account_type == '5':  # receptionist
                        return redirect('receptionistIndex')
                    elif account_type == '6':
                        return redirect('administrator_dashboard_index')
                    elif account_type == '7':
                        return redirect('accountant_dashboard')
                    elif account_type == '8':
                        return redirect('club_dashboard_index')
                    elif account_type == '9':
                        return redirect('club_dashboard_index')
                    else:
                        return redirect('home')

                except UserProfile.DoesNotExist:
                    return redirect('home')
            else:
                context['error'] = "رمز التحقق غير صحيح."

        except User.DoesNotExist:
            context['error'] = "المستخدم غير موجود."

    return render(request, 'accounts/sign/otp_verify.html', context)


def resend_otp(request):
    """Resend OTP code"""

    if request.method == 'POST' and 'otp_user_id' in request.session:
        try:
            user_id = request.session['otp_user_id']
            user = User.objects.get(id=user_id)

            # Check if last OTP was sent less than 1 minute ago
            last_otp = OTP.objects.filter(user=user).first()
            if last_otp and timezone.now() - last_otp.created_at < timedelta(minutes=1):
                return JsonResponse({
                    'success': False,
                    'message': 'يرجى الانتظار دقيقة واحدة قبل إعادة الإرسال'
                })

            # Generate new OTP
            otp_code = generate_otp()
            otp_record = OTP.objects.update_or_create(
                user=user,
                defaults={
                    "otp_code": otp_code,
                    "created_at": timezone.now(),
                    "delivery_method": last_otp.delivery_method if last_otp else "email"
                }
            )[0]

            # Send based on previous method
            if last_otp and last_otp.delivery_method == 'whatsapp':
                phone_number = request.session.get('user_phone')
                user_name = request.session.get('user_name')

                def send_whatsapp_async():
                    send_whatsapp_otp(phone_number, otp_code, user_name)

                thread = threading.Thread(target=send_whatsapp_async)
                thread.start()

                return JsonResponse({
                    'success': True,
                    'message': 'تم إعادة إرسال رمز التحقق عبر الواتساب'
                })
            else:
                email = request.session.get('user_email')
                user_name = request.session.get('user_name')
                success, message = send_email_otp(email, otp_code, user_name)

                return JsonResponse({
                    'success': success,
                    'message': message if success else 'خطأ في إرسال البريد الإلكتروني'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في إعادة الإرسال: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'طلب غير صالح'})


import base64
from django.core.files.base import ContentFile

def handle_file_upload(file_field):
    """Convert uploaded file to base64 string"""
    if file_field:
        file_content = file_field.read()
        encoded_file = base64.b64encode(file_content).decode('utf-8')
        return encoded_file
    return None

from django.utils import timezone
def signup(request):
    context = {}
    account_type = request.POST.get('account_type', '3')  # Default to Student

    student_form = StudentProfileForm()
    director_form = DirectorSignupForm()
    receptionist_form = ReceptionistSignupForm()
    vendor_form = VendorRegistrationForm()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        print(f"DEBUG: Account type: {account_type}, Username: {username}, Email: {email}")

        if account_type == '4':  # Vendor registration
            if CoachProfile.objects.filter(email=email).exists():
                messages.error(request, "البريد الإلكتروني مسجل مسبقًا.")
                return redirect('signup')
        else:
            # Check if user already exists for other account types
            if User.objects.filter(username=username).exists():
                messages.error(request, "اسم المستخدم مأخوذ بالفعل.")
                return redirect('signup')
            elif User.objects.filter(email=email).exists():
                messages.error(request, "البريد الإلكتروني مسجل مسبقًا.")
                return redirect('signup')

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "اسم المستخدم مأخوذ بالفعل.")
            return redirect('signup')

        elif User.objects.filter(email=email).exists():
            messages.error(request, "البريد الإلكتروني مسجل مسبقًا.")
            return redirect('signup')

        else:
            if account_type == '4':  # Vendor Registration
                vendor_form = VendorRegistrationForm(request.POST, request.FILES)
                if vendor_form.is_valid():
                    try:
                        vendor = vendor_form.save(commit=False)
                        vendor.approval_status = 'pending'

                        vendor.club = get_main_club()

                        # Handle file uploads
                        if 'business_document_file' in request.FILES:
                            vendor.business_document_file = handle_file_upload(request.FILES['business_document_file'])

                        if 'commercial_registration_certificate' in request.FILES:
                            vendor.commercial_registration_certificate = handle_file_upload(
                                request.FILES['commercial_registration_certificate'])

                        if 'tax_certificate' in request.FILES:
                            vendor.tax_certificate = handle_file_upload(request.FILES['tax_certificate'])

                        if 'store_logo' in request.FILES:
                            vendor.store_logo_base64 = handle_file_upload(request.FILES['store_logo'])

                        if 'profile_image' in request.FILES:
                            vendor.profile_image_base64 = handle_file_upload(request.FILES['profile_image'])

                        # Handle profile image if uploaded
                        profile_image = request.FILES.get('profile_image')
                        if profile_image:
                            try:
                                image_data = profile_image.read()
                                base64_encoded = base64.b64encode(image_data).decode('utf-8')
                                vendor.profile_image_base64 = base64_encoded
                            except Exception as e:
                                messages.error(request, f"خطأ في معالجة الصورة: {e}")
                                return redirect('signup')

                        # Handle business document file if uploaded
                        business_doc = request.FILES.get('business_document_file')
                        if business_doc:
                            try:
                                # Check file type
                                if not business_doc.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                                    messages.error(request, "يجب أن يكون الملف من نوع PDF أو صورة")
                                    return redirect('signup')

                                # Read and encode the file
                                file_data = business_doc.read()
                                base64_encoded = base64.b64encode(file_data).decode('utf-8')
                                vendor.business_document_file = base64_encoded
                            except Exception as e:
                                messages.error(request, f"خطأ في معالجة الملف: {e}")
                                return redirect('signup')

                        vendor.save()

                        # Send notification to club director
                        send_vendor_approval_notification(vendor)

                        messages.success(request,
                                         "تم تسجيل طلبك بنجاح! سيتم مراجعة طلبك من قبل إدارة المنصة وسيتم التواصل معك قريباً.")
                        return redirect('vendor_status', vendor_id=vendor.id)

                    except Exception as e:
                        messages.error(request, f"حدث خطأ غير متوقع: {e}")
                        return redirect('signup')
                else:
                    # Print form errors for debugging
                    print(vendor_form.errors)
                    messages.error(request, "حدث خطأ في بيانات التسجيل، يرجى التحقق منها.")

            elif account_type == '3':
                student_form = StudentProfileForm(request.POST, request.FILES)
                if student_form.is_valid():
                    user = User.objects.create_user(username=username, email=email, password=password)
                    student_profile = student_form.save(commit=False)
                    profile_image = request.FILES.get('profile_image_base64')
                    if profile_image:
                        try:
                            image_data = profile_image.read()
                            base64_encoded = base64.b64encode(image_data).decode('utf-8')
                            student_profile.profile_image_base64 = base64_encoded
                        except Exception as e:
                            messages.error(request, f"خطأ في معالجة الصورة: {e}")
                            return redirect('signup')

                    student_profile.save()
                    UserProfile.objects.create(user=user, account_type='3', student_profile=student_profile)

                    messages.success(request, "تم إنشاء حساب العميل بنجاح! يمكنك الآن تسجيل الدخول.")
                    return redirect('signin')
                else:
                    messages.error(request, "حدث خطأ في بيانات التسجيل، يرجى التحقق منها.")

            elif account_type == '2':  # Director Sign-Up
                director_form = DirectorSignupForm(request.POST, request.FILES)
                if director_form.is_valid():
                    try:
                        # **Step 1: Create the User first**
                        user = User.objects.create_user(username=username, email=email, password=password)

                        # **Step 2: Validate City Selection**
                        city = director_form.cleaned_data['city']
                        from .fields import citys
                        valid_city_values = [c[0] for c in citys]
                        if city not in valid_city_values:
                            messages.error(request, "اختيار المدينة غير صالح.")
                            return redirect('signup')

                        # **Step 3: Check for Existing Club**
                        club_name = director_form.cleaned_data['club_name']
                        existing_club = ClubsModel.objects.filter(name=club_name).first()
                        if existing_club:
                            messages.error(request, "اسم الصالون مستخدم بالفعل.")
                            return redirect('signup')

                        # **Step 4: Create the Club instance**
                        club = ClubsModel.objects.create(
                            name=club_name,
                            city=city,
                            street=director_form.cleaned_data['street'],
                            district=director_form.cleaned_data.get('district'),
                            about=director_form.cleaned_data.get('about'),
                            desc=director_form.cleaned_data.get('desc'),
                            club_profile_image_base64=director_form.cleaned_data.get('club_profile_image_base64', None),
                            current_plan_id=1  # Set to free plan by default
                        )

                        # **Step 5: Create Director Profile linked to the Club**
                        director_profile = DirectorProfile.objects.create(
                            full_name=director_form.cleaned_data['username'],
                            phone=director_form.cleaned_data['phone'],
                            club=club,
                            about=director_form.cleaned_data.get('about')
                        )

                        # **Step 6: Create UserProfile linked to the DirectorProfile**
                        UserProfile.objects.create(user=user, account_type='2', director_profile=director_profile)

                        # **Step 7: Create default free subscription**
                        Subscription.objects.create(
                            user=user,
                            club=club,
                            plan_id='1',
                            plan_name='الباقة المجانية',
                            amount=0.00,
                            status='active',
                            start_date=timezone.now(),
                            end_date=timezone.now() + timedelta(days=365)  # Free plan for 1 year
                        )

                        messages.success(request, f"تم إنشاء النادي {club_name} بنجاح!")
                        # **Redirect to subscription info page instead of signin**
                        return redirect('subscription_info')

                    except Exception as e:
                        messages.error(request, f"حدث خطأ غير متوقع: {e}")
                        return redirect('signup')

                else:
                    messages.error(request, "حدث خطأ في التسجيل، يرجى مراجعة البيانات.")

            elif account_type == '5':  # Receptionist Sign-Up
                receptionist_form = ReceptionistSignupForm(request.POST)
                if receptionist_form.is_valid():
                    try:
                        # Create User
                        user = User.objects.create_user(
                            username=receptionist_form.cleaned_data['username'],
                            email=receptionist_form.cleaned_data['email'],
                            password=receptionist_form.cleaned_data['password']
                        )

                        # Create Receptionist Profile
                        receptionist_profile = ReceptionistProfile.objects.create(
                            full_name=receptionist_form.cleaned_data['full_name'],
                            phone=receptionist_form.cleaned_data['phone'],
                            email=receptionist_form.cleaned_data['email'],
                            club=receptionist_form.cleaned_data['club'],
                            about=receptionist_form.cleaned_data.get('about')
                        )

                        # Create UserProfile
                        UserProfile.objects.create(
                            user=user,
                            account_type='5',
                            receptionist_profile=receptionist_profile
                        )

                        messages.success(request, "تم إنشاء حساب الموظف بنجاح! يمكنك الآن تسجيل الدخول.")
                        return redirect('signin')

                    except Exception as e:
                        messages.error(request, f"حدث خطأ غير متوقع: {e}")
                        return redirect('signup')

            # elif account_type == '6':
            #     administrator_form = AdministratorSignupForm(request.POST)
            #     if administrator_form.is_valid():
            #         try:
            #             # Create User
            #             user = User.objects.create_user(
            #                 username=administrator_form.cleaned_data['username'],
            #                 email=administrator_form.cleaned_data['email'],
            #                 password=administrator_form.cleaned_data['password']
            #             )
            #
            #             # Create administrator Profile
            #             administrator_profile = ReceptionistProfile.objects.create(
            #                 full_name=administrator_form.cleaned_data['full_name'],
            #                 phone=administrator_form.cleaned_data['phone'],
            #                 email=administrator_form.cleaned_data['email'],
            #                 club=administrator_form.cleaned_data['club'],
            #                 about=administrator_form.cleaned_data.get('about')
            #             )
            #
            #             # Create UserProfile
            #             UserProfile.objects.create(
            #                 user=user,
            #                 account_type='6',
            #                 administrator_profile=administrator_profile
            #             )
            #
            #             messages.success(request, "تم إنشاء حساب الاداري بنجاح! يمكنك الآن تسجيل الدخول.")
            #             return redirect('signin')
            #
            #         except Exception as e:
            #             messages.error(request, f"حدث خطأ غير متوقع: {e}")
            #             return redirect('signup')

    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'accounts/sign/signup.html', {
        'student_form': student_form,
        'director_form': director_form,
        'receptionist_form': receptionist_form,
        # 'administrator_form': administrator_form,
        'account_type': account_type,
        'vendor_form': vendor_form,
    })


def send_vendor_approval_notification(vendor):
    """Send email notification to club director about new vendor registration"""
    try:
        # Get the director's email - using the specific email you provided
        director_email = "naghammohamed287@gmail.com"

        subject = f"طلب تسجيل بائع جديد - {vendor.business_name}"
        message = f"""
        تم تسجيل طلب بائع جديد يحتاج إلى موافقتك:
        
        الاسم: {vendor.full_name}
        النشاط التجاري: {vendor.business_name}
        نوع النشاط: {vendor.activity_type.name}
        الهاتف: {vendor.phone}
        البريد الإلكتروني: {vendor.email}
        المدينة: {vendor.city}
        الحي: {vendor.district}
        
        يرجى الدخول إلى لوحة التحكم لمراجعة الطلب.
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [director_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending email notification: {e}")






def subscription_info(request):
    """
    Display subscription information page after successful director signup
    """
    context = {
        'LANGUAGE_CODE': translation.get_language()
    }
    return render(request, 'accounts/subscription_info.html', context)





def signout(request):
    logout(request)
    messages.success(request, "تم تسجيل الخروج بنجاح.")
    return redirect('landingIndex')

import os
import json
from django.conf import settings
def director_pricing(request):
    """
    Display pricing plans for director signup
    """
    # Check if director signup data exists in session
    if 'director_signup_data' not in request.session:
        messages.error(request, "يجب إكمال عملية التسجيل أولاً.")
        return redirect('signup')

    # Load pricing data from JSON file
    json_file_path = os.path.join(settings.BASE_DIR, 'pages/index.json')

    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            pricing = data.get('pricing', [])

            for i, plan in enumerate(pricing, 1):
                if 'id' not in plan:
                    plan['id'] = i
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback pricing data
        pricing = [
            {
                'id': 1,
                'name': 'الباقة الأساسية',
                'price': '99 ر.س',
                'features': ['إدارة المواعيد', 'قاعدة بيانات العملاء', 'التقارير الأساسية']
            },
            {
                'id': 2,
                'name': 'الباقة المتقدمة',
                'price': '199 ر.س',
                'features': ['جميع مميزات الأساسية', 'التسويق عبر الرسائل', 'التقارير المتقدمة']
            },
        ]

    context = {
        'pricing': pricing,
        'LANGUAGE_CODE': translation.get_language(),
        'director_data': request.session['director_signup_data']
    }

    return render(request, 'accounts/director_pricing.html', context)


def select_pricing_plan(request, plan_id):
    """
    Handle pricing plan selection for director - redirect to payment
    """
    if request.method == 'POST':
        # Check if director signup data exists in session
        if 'director_signup_data' not in request.session:
            messages.error(request, "يجب إكمال عملية التسجيل أولاً.")
            return redirect('signup')

        # Redirect to checkout page for payment
        return redirect('director_checkout', plan_id=plan_id)

    return redirect('director_pricing')



from .pay_api import generate_token, initiate_payment, execute_payment

def director_checkout(request, plan_id):
    """
    Handle payment initiation for director signup
    """
    if 'director_signup_data' not in request.session:
        messages.error(request, "يجب إكمال عملية التسجيل أولاً.")
        return redirect('signup')

    json_file_path = os.path.join(settings.BASE_DIR, 'pages/index.json')

    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            pricing = data.get('pricing', [])
    except (FileNotFoundError, json.JSONDecodeError):
        pricing = [
            {'id': 1, 'name': 'الباقة الأساسية', 'price': '99 ر.س', 'amount': 99.0},
            {'id': 2, 'name': 'الباقة المتقدمة', 'price': '199 ر.س', 'amount': 199.0},
        ]

    selected_plan = None
    plan_id_int = int(plan_id)
    plan_id_str = str(plan_id)

    for plan in pricing:
        plan_id_from_json = plan.get('id')
        print(f"Looking for plan_id: {plan_id} (type: {type(plan_id)})")
        print(f"Available plans: {[{'id': p.get('id'), 'type': type(p.get('id'))} for p in pricing]}")
        if (plan_id_from_json == plan_id_int or
                plan_id_from_json == plan_id_str or
                str(plan_id_from_json) == plan_id_str):
            selected_plan = plan
            break

    if not selected_plan:
        messages.error(request, "الباقة المحددة غير موجودة.")
        return redirect('director_pricing')

    request.session['selected_plan'] = selected_plan

    if request.method == "POST":
        mobile = request.POST.get('mobile')
        if not mobile:
            messages.error(request, "يرجى إدخال رقم الجوال.")
            return render(request, 'accounts/director_checkout.html', {
                'plan': selected_plan,
                'director_data': request.session['director_signup_data']
            })

        try:
            token_data, token_headers = generate_token()
            token = token_headers.get("X-Security-Token")
            session_id = token_headers.get("X-Session-Id")

            amount = selected_plan.get('amount', 99.0)
            init_data, init_headers = initiate_payment(token, session_id, amount=amount, mobile=mobile)

            otp_reference = init_data["body"]["otpReference"]
            verification_token = init_headers.get("X-Verification-Token")

            request.session["urpay_token"] = token
            request.session["urpay_session_id"] = session_id
            request.session["urpay_verification_token"] = verification_token
            request.session["urpay_otp_reference"] = otp_reference
            request.session["payment_mobile"] = mobile

            messages.success(request, "تم إرسال رمز التحقق إلى رقم جوالك.")
            return redirect("director_verify_otp")

        except Exception as e:
            messages.error(request, f"حدث خطأ في عملية الدفع: {str(e)}")
            return render(request, 'accounts/director_checkout.html', {
                'plan': selected_plan,
                'director_data': request.session['director_signup_data']
            })

    return render(request, 'accounts/director_checkout.html', {
        'plan': selected_plan,
        'director_data': request.session['director_signup_data']
    })


def director_verify_otp(request):
    """
    Handle OTP verification and payment execution
    """
    required_keys = ['director_signup_data', 'selected_plan', 'urpay_token',
                     'urpay_session_id', 'urpay_verification_token', 'urpay_otp_reference']

    for key in required_keys:
        if key not in request.session:
            messages.error(request, "انتهت صلاحية الجلسة. يرجى البدء من جديد.")
            return redirect('signup')

    if request.method == "POST":
        otp = request.POST.get('otp')
        if not otp:
            messages.error(request, "يرجى إدخال رمز التحقق.")
            return render(request, 'accounts/director_verify_otp.html', {
                'plan': request.session['selected_plan'],
                'mobile': request.session.get('payment_mobile', '')
            })

        try:
            token = request.session["urpay_token"]
            session_id = request.session["urpay_session_id"]
            verification_token = request.session["urpay_verification_token"]
            otp_reference = request.session["urpay_otp_reference"]
            mobile = request.session.get("payment_mobile", "+966568595106")
            amount = request.session['selected_plan'].get('amount', 99.0)

            payment_result = execute_payment(
                token, session_id, verification_token,
                otp_reference, otp, amount, mobile
            )

            if payment_result.get("body", {}).get("status") == "SUCCESS":
                return complete_director_signup_after_payment(request, payment_result)
            else:
                messages.error(request, "فشلت عملية الدفع. يرجى المحاولة مرة أخرى.")
                return render(request, 'accounts/director_verify_otp.html', {
                    'plan': request.session['selected_plan'],
                    'mobile': mobile
                })

        except Exception as e:
            messages.error(request, f"حدث خطأ في تأكيد الدفع: {str(e)}")
            return render(request, 'accounts/director_verify_otp.html', {
                'plan': request.session['selected_plan'],
                'mobile': request.session.get('payment_mobile', '')
            })

    return render(request, 'accounts/director_verify_otp.html', {
        'plan': request.session['selected_plan'],
        'mobile': request.session.get('payment_mobile', '')
    })

def complete_director_signup_after_payment(request, payment_result):
    """
    Complete director account creation after successful payment
    """
    try:
        signup_data = request.session['director_signup_data']
        plan_data = request.session['selected_plan']

        # **Step 1: Create the User**
        user = User.objects.create_user(
            username=signup_data['username'],
            email=signup_data['email'],
            password=signup_data['password']
        )

        # **Step 2: Create the Club instance**
        club = ClubsModel.objects.create(
            name=signup_data['club_name'],
            city=signup_data['city'],
            street=signup_data['street'],
            district=signup_data.get('district'),
            about=signup_data.get('about'),
            desc=signup_data.get('desc'),
            club_profile_image_base64=signup_data.get('club_profile_image_base64', None)
        )

        # **Step 3: Create Director Profile linked to the Club**
        director_profile = DirectorProfile.objects.create(
            full_name=signup_data['username'],
            phone=signup_data['phone'],
            club=club,
            about=signup_data.get('about')
        )

        # **Step 4: Create UserProfile linked to the DirectorProfile**
        UserProfile.objects.create(
            user=user,
            account_type='2',
            director_profile=director_profile
        )

        # **Step 5: Create Subscription record**
        subscription = Subscription.create_subscription(
            user=user,
            club=club,
            plan_data=plan_data,
            payment_reference=payment_result.get("body", {}).get("transactionId"),
            duration_days=30  # 30 days subscription
        )

        # **Step 6: Store current plan ID in club for quick access**
        club.current_plan_id = int(plan_data['id'])
        club.save()

        # Clear session data
        session_keys_to_clear = [
            'director_signup_data', 'selected_plan', 'urpay_token',
            'urpay_session_id', 'urpay_verification_token',
            'urpay_otp_reference', 'payment_mobile'
        ]

        for key in session_keys_to_clear:
            if key in request.session:
                del request.session[key]

        messages.success(request, f"تم إنشاء الصالون {signup_data['club_name']} وتفعيل باقة {plan_data['name']} بنجاح! يمكنك الآن تسجيل الدخول.")
        return redirect('signin')

    except Exception as e:
        messages.error(request, f"حدث خطأ في إنشاء الحساب بعد الدفع: {e}")
        return redirect('signup')

def generate_reset_token():
    """Generate a secure random token for password reset"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def forgot_password(request):
    """Handle forgot password request - send reset email"""
    context = {}
    form = ForgotPasswordForm()

    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()

            user = User.objects.filter(email=email).first()

            if user:
                reset_token = generate_reset_token()

                PasswordResetToken.objects.filter(user=user).delete()

                PasswordResetToken.objects.create(
                    user=user,
                    token=reset_token,
                    expires_at=now() + timedelta(hours=1)
                )

                try:
                    reset_url = request.build_absolute_uri(f'/auth/reset-password/{reset_token}/')

                    send_mail(
                        subject="إعادة تعيين كلمة المرور - Reset Password",
                        message=f"""
مرحباً {user.username},

لقد تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بك.

اضغط على الرابط التالي لإعادة تعيين كلمة المرور:
{reset_url}

هذا الرابط صالح لمدة ساعة واحدة فقط.

إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذه الرسالة.

---

Hello {user.username},

We received a request to reset your password.

Click the following link to reset your password:
{reset_url}

This link is valid for 1 hour only.

If you didn't request a password reset, please ignore this email.
                        """,
                        from_email="noreply@yourdomain.com",
                        recipient_list=[email],
                        fail_silently=False,
                    )

                    messages.success(request, "تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني.")
                    return redirect('signin')

                except Exception as e:
                    messages.error(request, f"حدث خطأ في إرسال البريد الإلكتروني: {str(e)}")
            else:
                messages.success(request, "إذا كان البريد الإلكتروني مسجلاً لدينا، ستتلقى رابط إعادة تعيين كلمة المرور.")
                return redirect('signin')

    context.update({
        'form': form,
        'LANGUAGE_CODE': translation.get_language()
    })

    return render(request, 'accounts/sign/forgot_password.html', context)

def reset_password(request, token):
    """Handle password reset with token"""
    context = {}

    reset_token = PasswordResetToken.objects.filter(
        token=token,
        expires_at__gt=now()
    ).first()

    if not reset_token:
        messages.error(request, "رابط إعادة تعيين كلمة المرور غير صالح أو منتهي الصلاحية.")
        return redirect('forgot_password')

    form = ResetPasswordForm()

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']

            user = reset_token.user
            user.set_password(new_password)
            user.save()

            reset_token.delete()

            messages.success(request, "تم تغيير كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول.")
            return redirect('signin')

    context.update({
        'form': form,
        'token': token,
        'user': reset_token.user,
        'LANGUAGE_CODE': translation.get_language()
    })

    return render(request, 'accounts/sign/reset_password.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from club_dashboard.models import SubCategory


@login_required
def select_subcategories(request):
    try:
        user_profile = request.user.userprofile
        if user_profile.account_type != '4':  # Not a coach/vendor
            messages.error(request, "هذه الصفحة مخصصة للتجار فقط")
            return redirect('home')

        coach_profile = user_profile.Coach_profile
        if not coach_profile.activity_type:
            messages.error(request, "يجب تحديد نوع النشاط أولاً")
            return redirect('coach_dashboard')

        if request.method == 'POST':
            selected_subcategories = request.POST.getlist('subcategories')
            coach_profile.subcategories.set(selected_subcategories)
            messages.success(request, "تم حفظ التخصصات بنجاح!")
            return redirect('coachIndex')  # Redirect to coach dashboard after selection

        # Get subcategories for their activity type
        from club_dashboard.models import SubCategory
        subcategories = SubCategory.objects.filter(category=coach_profile.activity_type)

        return render(request, 'accounts/select_subcategories.html', {
            'subcategories': subcategories,
            'activity_type': coach_profile.activity_type,
            'selected_subcategories': coach_profile.subcategories.values_list('id', flat=True)
        })

    except Exception as e:
        messages.error(request, f"حدث خطأ: {str(e)}")
        return redirect('home')


from django.http import JsonResponse
from .fields import REGIONS_AND_CITIES

def get_cities_by_region(request):
    region = request.GET.get('region', '')
    cities = REGIONS_AND_CITIES.get(region, [])
    return JsonResponse({'cities': cities})




from datetime import datetime
from accountant_dashboard.models import TermsAndConditions

def terms_and_conditions(request):
    # Try to get club-specific terms if user is associated with a club
    terms_content = None
    try:
        # You need to get a specific instance, not access the class
        terms_instance = TermsAndConditions.objects.first()  # or some other query
        terms_content = terms_instance.content if terms_instance else None
    except TermsAndConditions.DoesNotExist:
        terms_content = None


    # Fallback to default terms if no club-specific terms found
    if not terms_content:
        terms_content = """
        <h2>الشروط والأحكام العامة</h2>
        <p>هذه هي الشروط والأحكام العامة للمنصة.</p>
        """

    context = {
        'terms_content': terms_content,
        'current_date': datetime.now().strftime("%Y-%m-%d"),
        'LANGUAGE_CODE': translation.get_language()
    }
    return render(request, 'accounts/sign/terms_and_conditions.html', context)