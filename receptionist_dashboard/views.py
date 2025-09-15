from django.shortcuts import render, redirect, get_object_or_404
from club_dashboard.models import SalonAppointment
from django.contrib.auth.decorators import login_required
from .forms import SalonBookingForm ,ServiceSelectionForm,ReceptionistProfileForm
from .models import SalonBooking ,BookingService
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import UserProfile ,StudentProfile
from django.contrib.auth.models import User
from club_dashboard.utils import send_notification
from accounts.forms import StudentProfileForm
from datetime import datetime, timedelta
from django.db import models , transaction
from students.models import ServicesModel
from django.forms import formset_factory
import base64
from django.views.decorators.http import require_GET
from django.utils import translation
from django.utils.translation import get_language

# Helper function to get user's club
def get_user_club(user):
    user_profile = user.userprofile
    club = None
    if user_profile.account_type == '3':  # Student
        club = user_profile.student_profile.club if hasattr(user_profile, 'student_profile') else None
    elif user_profile.account_type == '4':  # Coach
        club = user_profile.Coach_profile.club if hasattr(user_profile, 'Coach_profile') else None
    elif user_profile.account_type == '2':  # Director
        club = user_profile.director_profile.club if hasattr(user_profile, 'director_profile') else None
    elif user_profile.account_type == '5':  # Receptionist
        club = user_profile.receptionist_profile.club if hasattr(user_profile, 'receptionist_profile') else None
    return club


@login_required
def index(request):
    club = get_user_club(request.user)
    if not club:
        messages.error(request, "No club assigned to your profile. Please contact an administrator.")
        return redirect('signin')

    # Verify user is a receptionist
    if request.user.userprofile.account_type != '5':
        return redirect('signin')

    # Get students count and list
    students = UserProfile.objects.filter(
        account_type='3',
        student_profile__club=club
    ).select_related('user', 'student_profile')
    valid_students = [student for student in students if student.student_profile]

    students_count = UserProfile.objects.filter(
        account_type='3',
        student_profile__club=club
    ).count()

    # Get coaches count
    coaches_count = UserProfile.objects.filter(
        account_type='4',
        Coach_profile__club=club
    ).count()

    # Get receptionist profile
    receptionist_profile = request.user.userprofile.receptionist_profile

    # Get counts for dashboard cards
    messages_count = 0  # Replace with actual message count query if available
    tickets_count = CoachReceptionistTicket.objects.filter(receptionist=receptionist_profile).count()

    context = {
        'receptionist': receptionist_profile,
        'club': club,
        'students': valid_students,
        'coaches_count': coaches_count,
        'messages_count': messages_count,
        'students_count': students_count,
        'tickets_count': tickets_count,
        'LANGUAGE_CODE': translation.get_language()
    }
    return render(request, 'receptionist_dashboard/index.html', context)


from accounts.models import CoachProfile



def check_coach_availability_by_id(day, start_time, end_time, coach_id, club):
    """
    Check if a coach is available at the given time slot using coach ID
    Returns True if there are conflicts, False if available
    """
    # Check conflicts in BookingService model using coach ID
    booking_services_conflicts = BookingService.objects.filter(
        coach_id=coach_id,
        booking__appointment__day=day,
        booking__appointment__available=False,
        booking__appointment__club=club
    ).filter(
        models.Q(
            booking__appointment__start_time__lt=end_time,
            booking__appointment__end_time__gt=start_time
        )
    )

    # Also check primary coach conflicts
    primary_coach_conflicts = SalonBooking.objects.filter(
        primary_coach_id=coach_id,
        appointment__day=day,
        appointment__available=False,
        appointment__club=club
    ).filter(
        models.Q(
            appointment__start_time__lt=end_time,
            appointment__end_time__gt=start_time
        )
    )

    return booking_services_conflicts.exists() or primary_coach_conflicts.exists()

@login_required
def get_service_info(request, service_id):
    """
    Returns JSON with service information including duration and associated coaches
    """
    try:
        service = ServicesModel.objects.get(id=service_id)
        coaches = service.coaches.all()

        coach_data = [
            {
                'id': coach.id,
                'name': coach.full_name
            } for coach in coaches
        ]

        return JsonResponse({
            'duration': service.duration,
            'coaches': coach_data
        })
    except ServicesModel.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)



def check_coach_availability(day, start_time, end_time, coach_id, club):
    """
    Legacy function - redirects to ID-based check
    """
    return check_coach_availability_by_id(day, start_time, end_time, coach_id, club)

@login_required
def get_service_duration(request, service_id):
    try:
        service = ServicesModel.objects.get(id=service_id)
        return JsonResponse({'duration': service.duration})
    except ServicesModel.DoesNotExist:
        return JsonResponse({'duration': 0})







def viewStudentss(request):
    context = {}
    """Displays all students in the club."""
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    students = UserProfile.objects.filter(
        account_type='3',
        student_profile__club=club
    ).select_related('user', 'student_profile')

    valid_students = [student for student in students if student.student_profile]
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'receptionist_dashboard/students/viewStudents.html', {'students': valid_students,'club': club})


def addStudent(request):
    context = {}
    """Adds a new student to the club."""
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    form = StudentProfileForm()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('addStudentFromReceptionist')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use.")
            return redirect('addStudentFromReceptionist')

        form = StudentProfileForm(request.POST)
        if form.is_valid():
            student = User.objects.create(username=username, email=email)
            if password:
                student.set_password(password)
            student.save()

            student_profile = form.save(commit=False)
            student_profile.user = student
            student_profile.club = club  # تعيين النادي هنا
            student_profile.save()

            UserProfile.objects.create(user=student, account_type='3', student_profile=student_profile)

            messages.success(request, "client added successfully.")
            return redirect('viewStudentss')
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, f"Form validation failed: {form.errors}")
    from django import forms
    if 'club' in form.fields:
        form.fields['club'].widget = forms.HiddenInput()
        form.initial['club'] = club.id

    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'receptionist_dashboard/students/addStudent.html', {'form': form, 'club': club})


@login_required
def editStudentt(request, id):
    context = {}
    """Edits an existing student's details."""
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    student_profile = get_object_or_404(StudentProfile, id=id)
    if student_profile.club != club:
        messages.error(request, "ليس لديك صلاحية لتعديل هذا الطالب.")
        return redirect('viewStudentss')

    student = get_object_or_404(User, userprofile__student_profile=student_profile)

    form = StudentProfileForm(instance=student_profile)

    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=new_username).exclude(id=student.id).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'receptionist_dashboard/students/editStudent.html', {
                'form': form,
                'student': student
            })

        if User.objects.filter(email=new_email).exclude(id=student.id).exists():
            messages.error(request, "Email is already in use.")
            return render(request, 'receptionist_dashboard/students/editStudent.html', {
                'form': form,
                'student': student
            })

        form = StudentProfileForm(request.POST, instance=student_profile)
        if form.is_valid():
            student.username = new_username
            student.email = new_email
            if password:
                student.set_password(password)
            student.save()

            student_profile = form.save(commit=False)
            student_profile.user = student
            student_profile.club = club
            student_profile.save()

            messages.success(request, "Student profile updated successfully.")
            return redirect('viewStudentss')
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, f"Form validation failed: {form.errors}")

    from django import forms
    if 'club' in form.fields:
        form.fields['club'].widget = forms.HiddenInput()
        form.initial['club'] = club.id
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'receptionist_dashboard/students/editStudent.html', {
        'form': form,
        'student': student,
        'club' : club
    })



@login_required
def deleteStudentt(request, id):
    """Deletes a student from the club."""
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    student_profile = get_object_or_404(StudentProfile, id=id)
    if student_profile.club != club:
        messages.error(request, "ليس لديك صلاحية لحذف هذا الطالب.")
        return redirect('viewStudentss')

    student = get_object_or_404(User, userprofile__student_profile=student_profile)

    student_name = student.username

    student_profile.delete()
    student.delete()



    messages.success(request, "Client has been deleted successfully.")
    return redirect('viewStudentss')


@login_required
def view_receptionist_profile(request):
    club = get_user_club(request.user)
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        receptionist = user_profile.receptionist_profile

        if not receptionist:
            messages.error(request, "لا يوجد ملف شخصي لموظف الاستقبال")
            return redirect('receptionistIndex')

        context = {
            'receptionist': receptionist,
            'userprofile': user_profile ,
            'club': club,
        }
        context['LANGUAGE_CODE'] = translation.get_language()
        return render(request, 'accounts/profiles/receptionist/ViewReceptionistProfile.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, "لا يوجد ملف شخصي")
        return redirect('receptionistIndex')

@login_required
def edit_receptionist_profile(request):
    club = get_user_club(request.user)
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        receptionist = user_profile.receptionist_profile

        if not receptionist:
            messages.error(request, "لا يوجد ملف شخصي لموظف الاستقبال")
            return redirect('receptionistIndex')

        if request.method == 'POST':
            form = ReceptionistProfileForm(request.POST, instance=receptionist)
            if form.is_valid():
                receptionist_profile = form.save(commit=False)

                if 'profile_image_base64' in request.FILES:
                    image_file = request.FILES['profile_image_base64']
                    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

                    receptionist_profile.profile_image_base64 = f"data:image/{image_file.content_type.split('/')[-1]};base64,{encoded_image}"
                    user_profile.profile_image_base64 = receptionist_profile.profile_image_base64
                    user_profile.save()

                receptionist_profile.save()
                messages.success(request, "تم تحديث الملف الشخصي بنجاح")
                return redirect('view_receptionist_profile')
        else:
            form = ReceptionistProfileForm(instance=receptionist)

        context = {
            'form': form,
            'receptionist': receptionist,
            'club' : club
        }
        context['LANGUAGE_CODE'] = translation.get_language()
        return render(request, 'accounts/settings/receptionist/EditReceptionistProfile.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, "لا يوجد ملف شخصي")
        return redirect('receptionistIndex')

@require_GET
def service_coach(request, service_id):
    """API endpoint to get coach associated with a service"""
    try:
        service = ServicesModel.objects.get(id=service_id)
        if service.coach:
            return JsonResponse({
                'coach_id': service.coach.id,
                'coach_name': service.coach.full_name
            })
        return JsonResponse({'message': 'No coach associated with this service'}, status=200)
    except ServicesModel.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone, translation
from django.db import transaction
from django.contrib.auth.models import User
from decimal import Decimal
import logging
from students.models import ServiceOrderModel,ServicesModel,Order,OrderItem

logger = logging.getLogger(__name__)

@login_required
def student_subscriptions(request, student_id):
    """View to display student's subscriptions and allow adding new ones"""
    context = {}
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم." if translation.get_language() == 'ar' else "No club assigned to this user.")
        return redirect('index')

    student_user = get_object_or_404(User, id=student_id)
    try:
        student = student_user.userprofile
        if student.account_type != '3' or student.student_profile.club != club:
            messages.error(request, "غير مسموح لك بعرض اشتراكات هذا اللاعب." if translation.get_language() == 'ar' else "You're not allowed to view this student's subscriptions.")
            return redirect('viewStudentss')
    except:
        messages.error(request, "لاعب غير صحيح." if translation.get_language() == 'ar' else "Invalid student.")
        return redirect('viewStudentss')

    # Fixed: Added prefetch_related for coaches (without __user for now)
    subscriptions = ServiceOrderModel.objects.filter(
        student=student_user
    ).select_related('service').prefetch_related('service__coaches').order_by('-creation_date')

    # Also prefetch for available services
    available_services = ServicesModel.objects.filter(club=club).prefetch_related('coaches')

    context.update({
        'student': student,
        'subscriptions': subscriptions,
        'available_services': available_services,
        'current_time': timezone.now(),
        'LANGUAGE_CODE': translation.get_language(),
        'club': club
    })

    return render(request, 'receptionist_dashboard/students/student_subscriptions.html', context)


@login_required
def add_student_subscription(request, student_id):
    """Add a new subscription for a student (receptionist action)"""
    if request.method != 'POST':
        return redirect('student_subscriptions', student_id=student_id)

    club = get_user_club(request.user)
    lang = translation.get_language()

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم." if lang == 'ar' else "No club assigned to this user.")
        return redirect('index')

    student_user = get_object_or_404(User, id=student_id)
    try:
        student = student_user.userprofile
        if student.account_type != '3' or student.student_profile.club != club:
            messages.error(request, "غير مسموح لك بإضافة اشتراك لهذا اللاعب." if lang == 'ar' else "You're not allowed to add subscription for this student.")
            return redirect('viewStudentss')
    except:
        messages.error(request, "لاعب غير صحيح." if lang == 'ar' else "Invalid student.")
        return redirect('viewStudentss')

    service_id = request.POST.get('service_id')
    quantity = int(request.POST.get('quantity', 1))

    service = get_object_or_404(ServicesModel, id=service_id, club=club)

    try:
        with transaction.atomic():
            total_price = service.price * quantity

            order = Order.objects.create(
                user=student_user,
                club=club,
                total_price=total_price,
                status='confirmed',
                payment_method='credit_card',
                first_name=student.student_profile.full_name or student_user.username,
                last_name=student_user.username,
                email=student_user.email,
                phone=student.student_profile.phone or '',
                address='anything',
                city='anything',
                region='anything',
                postal_code='12345',
                notes=f'اشتراك تم إنشاؤه بواسطة موظف الاستقبال' if lang == 'ar' else 'Subscription created by receptionist'
            )

            OrderItem.objects.create(
                order=order,
                service=service,
                quantity=quantity,
                price=service.price
            )

            existing_service_order = ServiceOrderModel.objects.filter(
                student=student_user,
                service=service
            ).order_by('-end_datetime').first()

            if existing_service_order:
                if existing_service_order.end_datetime > timezone.now():
                    new_end_datetime = existing_service_order.end_datetime + timezone.timedelta(days=service.subscription_days * quantity)
                else:
                    new_end_datetime = timezone.now() + timezone.timedelta(days=service.subscription_days * quantity)

                existing_service_order.end_datetime = new_end_datetime
                existing_service_order.price += total_price
                existing_service_order.creation_date = timezone.now()
                existing_service_order.is_complited = False
                existing_service_order.save()

                subscription_action = 'تم تجديد الاشتراك' if lang == 'ar' else 'Subscription renewed'
            else:
                ServiceOrderModel.objects.create(
                    service=service,
                    student=student_user,
                    price=total_price,
                    is_complited=False,
                    end_datetime=timezone.now() + timezone.timedelta(days=service.subscription_days * quantity),
                    creation_date=timezone.now()
                )

                subscription_action = 'تم إنشاء اشتراك جديد' if lang == 'ar' else 'New subscription created'

            receptionist_name = request.user.username
            if hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'receptionist_profile'):
                receptionist_name = request.user.userprofile.receptionist_profile.full_name or request.user.username

            service_title =  service.title
            student_name = student.student_profile.full_name or student_user.username
            currency_symbol = 'ر.س' if lang == 'ar' else 'SAR'

            if lang == 'ar':
                notification_message = f"تم إنشاء اشتراك جديد بواسطة موظف الاستقبال 💎 {receptionist_name} للاعب {student_name}. الخدمة: {service_title}. المبلغ: {total_price} {currency_symbol}. الكمية: {quantity}. {subscription_action}."
            else:
                notification_message = f"New subscription created by receptionist 💎 {receptionist_name} for student {student_name}. Service: {service_title}. Amount: {total_price} {currency_symbol}. Quantity: {quantity}. {subscription_action}."

            send_notification(request.user, club, notification_message)

            if lang == 'ar':
                messages.success(request, f"تم إضافة الاشتراك بنجاح للاعب {student_name}. الخدمة: {service_title}")
            else:
                messages.success(request, f"Subscription added successfully for {student_name}. Service: {service_title}")

    except Exception as e:
        logger.error(f"Error adding subscription: {str(e)}")
        messages.error(request, f"حدث خطأ أثناء إضافة الاشتراك: {str(e)}" if lang == 'ar' else f"Error adding subscription: {str(e)}")

    return redirect('student_subscriptions', student_id=student_id)

from club_dashboard.models import Notification
def send_notification(user, club, message):
    """Helper function to send notifications to club director"""
    try:
        Notification.objects.create(
            club=club,
            message=message,
            is_read=False,
            created_at=timezone.now()
        )
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")


from coach_dashboard.models import CoachReceptionistTicket
@login_required
def receptionist_ticket_list(request):
    club = get_user_club(request.user)
    user_profile = request.user.userprofile
    if user_profile.account_type != '5':  # 5 is receptionist
        return redirect('home')

    receptionist_profile = user_profile.receptionist_profile
    tickets = CoachReceptionistTicket.objects.filter(receptionist=receptionist_profile).order_by('-created_at')
    return render(request, 'receptionist_dashboard/tickets/receptionist_ticket_list.html', {'tickets': tickets,'club': club})


@login_required
def update_ticket_status(request, ticket_id):
    user_profile = request.user.userprofile
    if user_profile.account_type != '5':  # Only receptionist can update status
        return redirect('home')

    ticket = get_object_or_404(CoachReceptionistTicket, id=ticket_id)
    if ticket.receptionist != user_profile.receptionist_profile:
        return redirect('receptionist_ticket_list')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(CoachReceptionistTicket.STATUS_CHOICES).keys():
            ticket.status = new_status
            ticket.save()

    return redirect('coach_ticket_detail', ticket_id=ticket.id)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from club_dashboard.models import RefundDispute, RefundDisputeMessage
from accounts.models import UserProfile
from django.http import HttpResponseForbidden


@login_required
def receptionist_refund_list(request):
    """List of refund disputes assigned to receptionist"""
    user_profile = request.user.userprofile

    # Verify receptionist access
    if not hasattr(user_profile, 'receptionist_profile'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')

    club = user_profile.receptionist_profile.club
    disputes = RefundDispute.objects.filter(
        current_stage='receptionist',
        order_item__product__club=club
    ).order_by('-created_at')

    # Status counts for dashboard
    status_counts = {
        'total': disputes.count(),
        'pending': disputes.filter(status='pending').count(),
        'escalated': disputes.filter(status='escalated').count(),
        'resolved': disputes.filter(status='resolved').count(),
    }

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['pending', 'escalated', 'resolved']:
        disputes = disputes.filter(status=status_filter)

    context = {
        'disputes': disputes,
        'status_counts': status_counts,
        'status_filter': status_filter,
        'club': club,
    }
    return render(request, 'receptionist_dashboard/refunds/refund_list.html', context)


@login_required
def receptionist_refund_detail(request, dispute_id):
    """Detailed view of a refund dispute for receptionist"""
    dispute = get_object_or_404(RefundDispute, id=dispute_id)
    user_profile = request.user.userprofile

    # Verify receptionist access and club match
    if not (hasattr(user_profile, 'receptionist_profile') and
            user_profile.receptionist_profile.club == (
                    dispute.order_item.product.club if dispute.order_item.product
                    else dispute.order_item.service.club)):
        return HttpResponseForbidden("You don't have permission to view this dispute.")

    # Check for automatic escalation
    dispute.check_for_escalation()

    if request.method == 'POST':
        message = request.POST.get('message')
        action = request.POST.get('action')

        if message:
            # Add new message to the conversation
            dispute.add_message(
                sender=user_profile,
                message=message,
                attachments=request.FILES.getlist('attachments')
            )
            messages.success(request, "Message sent successfully")

        elif action == 'escalate':
            if dispute.current_stage == 'receptionist':
                dispute.update_stage('director')
                dispute.status = 'escalated'
                dispute.save()
                messages.success(request, "Dispute escalated to director")
            else:
                messages.error(request, "You can only escalate in the receptionist review stage")

        elif action == 'resolve':
            if dispute.current_stage == 'receptionist':
                dispute.status = 'resolved'
                dispute.current_stage = 'resolved'
                dispute.resolved_at = timezone.now()
                dispute.save()
                messages.success(request, "Dispute marked as resolved")
            else:
                messages.error(request, "You can only resolve in the receptionist review stage")

        return redirect('receptionist_refund_detail', dispute_id=dispute.id)

    # Get all messages in the dispute
    conversation = dispute.messages.all().order_by('created_at')

    context = {
        'dispute': dispute,
        'order_item': dispute.order_item,
        'conversation': conversation,
        'can_escalate': dispute.current_stage == 'receptionist',
        'can_resolve': dispute.current_stage == 'receptionist',
        'can_message': dispute.current_stage in ['receptionist', 'director'],
        'time_remaining': (dispute.next_escalation_time - timezone.now()) if dispute.next_escalation_time else None,
        'club': user_profile.receptionist_profile.club,
    }
    return render(request, 'receptionist_dashboard/refunds/refund_detail.html', context)

