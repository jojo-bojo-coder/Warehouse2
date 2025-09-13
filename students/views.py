from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Sum, F, ExpressionWrapper, DecimalField
from django.contrib import messages
from club_dashboard.models import SalonAppointment,Notification,DashboardSettings
from django.core.paginator import Paginator
from receptionist_dashboard.models import SalonBooking,BookingService
from django.db import models , transaction
from datetime import datetime, timedelta
import datetime
from django.forms import formset_factory
from django.contrib.auth.decorators import login_required
from receptionist_dashboard.forms import SalonBookingForm ,ServiceSelectionForm
from django.http import JsonResponse
from .models import ProductsModel , CartItem,ServiceCartItem,OrderItem,Order,OrderCancellation
from accounts.models import UserProfile ,User,StudentProfile
from django import forms
import base64
from decimal import Decimal
from django.utils import translation
from django.utils.translation import get_language
from django.utils.formats import localize
from decimal import Decimal
import logging
import datetime
from django.utils import timezone





# Import necessary models
from .models import (
    Blog, ServicesModel, ServicesClassificationModel,
    ProductsModel, ProductsClassificationModel, ServiceOrderModel
)
from club_dashboard.models import Review  # ✅ Import Review from club_dashboard
from accounts.models import ClubsModel, CoachProfile, StudentProfile

# Import necessary forms
from .forms import ReviewForm


# from django.contrib import messages

import datetime
# Create your views here.

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


# Updated section in the index view
from django.db.models import Exists, OuterRef
def index(request):
    context = {}
    user = request.user
    print(f"User authenticated: {user.is_authenticated}")
    dashboard_settings = DashboardSettings.get_settings()

    try:
        userprofile = UserProfile.objects.get(user=user)
        student = userprofile.student_profile
        print(f"User: {user}, Profile: {getattr(user, 'userprofile', None)}")
        print(f"Student Profile: {getattr(userprofile, 'student_profile', None) if 'userprofile' in locals() else None}")
        print(f"Club: {getattr(student, 'club', None) if 'student' in locals() else None}")

        if not student:
            messages.error(request, "No student profile found for this user.")
            return redirect('signin')

        club = student.club
        student_identifier = student.full_name

        if not club:
            messages.error(request, "No club associated with this student.")
            return redirect('signin')

        coaches = CoachProfile.objects.filter(club=club)
        students = StudentProfile.objects.filter(club=club)



        # Fetch all services and products related to the club
        services = ServicesModel.objects.filter(club=club)
        products = ProductsModel.objects.filter(club=club)

        paid_service_subquery = OrderItem.objects.filter(
            order__user=request.user,
            order__status__in=['confirmed', 'completed'],  # Only paid/confirmed orders
            service=OuterRef('service')
        )

        active_service_orders = ServiceOrderModel.objects.filter(
            student=request.user,
            service__isnull=False,
        ).annotate(
            has_paid_order=Exists(paid_service_subquery)
        ).filter(
            has_paid_order=True
        ).select_related('service')

        # Filter to only include active subscriptions
        active_service_ids = []
        now = timezone.now()

        for order in active_service_orders:
            # Check if service subscription is still active (end_datetime is in the future)
            if order.end_datetime >= now:
                active_service_ids.append(order.service.id)

        print(f"Found {len(active_service_ids)} active service subscriptions for student")



        three_days_from_now = timezone.now() + datetime.timedelta(days=3)
        lang = translation.get_language()
        context['LANGUAGE_CODE'] = lang

        # **UPDATED**: Get only the latest service order for each service to avoid duplicate cards
        # Use raw SQL or annotations to get the latest order per service
        from django.db.models import Max

        # Get service IDs that have been paid for (confirmed or completed orders)
        paid_service_ids = OrderItem.objects.filter(
            order__user=user,
            order__status__in=['confirmed', 'completed'],  # Only paid/confirmed orders
            service__isnull=False
        ).values_list('service_id', flat=True).distinct()

        # Get the latest creation_date for each service that has been paid for
        latest_orders_subquery = ServiceOrderModel.objects.filter(
            student=user,
            service_id__in=paid_service_ids  # Only include services with paid orders
        ).values('service').annotate(
            latest_date=Max('creation_date')
        ).values('service', 'latest_date')

        # Get the actual service orders that match the latest dates
        service_orders = []
        for item in latest_orders_subquery:
            latest_order = ServiceOrderModel.objects.filter(
                student=user,
                service_id=item['service'],
                creation_date=item['latest_date'],
            ).select_related('service').first()
            if latest_order:
                service_orders.append(latest_order)

        # Sort by end_datetime descending to show most recent first
        service_orders = sorted(service_orders, key=lambda x: x.end_datetime, reverse=True)

        context['service_orders'] = service_orders
        context['today'] = timezone.now()  # Add today's date for the template

        return render(request, 'student/index.html', {
            'coaches': coaches,
            'students': students,
            'club': club,
            'services': services,
            'products': products,
            'service_orders': service_orders,
            'today': timezone.now(),
            'three_days_from_now': three_days_from_now,
            'show_employee_client_counts': dashboard_settings.show_employee_client_counts,
        })

    except UserProfile.DoesNotExist as e:
        print(f"UserProfile.DoesNotExist: {str(e)}")
        messages.error(request, "User profile not found.")
        return redirect('signin')
    except Exception as e:
        print(f"Unexpected exception: {str(e)}")
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('signin')



from coach_dashboard.models import Promotion
from django.core.paginator import PageNotAnInteger
from django.core.paginator import EmptyPage

def viewProducts(request):
    context = {}
    user = request.user
    club = user.userprofile.student_profile.club

    # Get all active promotions for products in this club
    active_promotions = Promotion.objects.filter(
        status='active',
        promotion_type='product',
        product__club=club
    ).select_related('product')

    # Get promoted product IDs
    promoted_product_ids = active_promotions.values_list('product_id', flat=True)

    # Get approved products - promoted first
    products = ProductsModel.objects.filter(
        club=club,
        is_enabled=True,
        approval_status='approved'
    ).order_by('-creation_date')

    # Add promotion info to each product
    promoted_products = []
    regular_products = []

    for product in products:
        if product.id in promoted_product_ids:
            product.is_promoted = True
            promotion = active_promotions.filter(product_id=product.id).first()
            promoted_products.append(product)
        else:
            product.is_promoted = False
            regular_products.append(product)

    # Combine lists with promoted first
    products = promoted_products + regular_products

    # Calculate totals using len() instead of count() for lists
    total_products = len(products)
    total_value = 0
    low_stock_count = 0
    out_of_stock_count = 0
    low_stock_threshold = 10

    for product in products:
        if hasattr(product, 'stock'):
            product_value = product.price * product.stock
            total_value += product_value

            if 0 < product.stock <= low_stock_threshold:
                low_stock_count += 1

            if product.stock == 0:
                out_of_stock_count += 1

    # Pagination
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page', 1)
    try:
        paginated_products = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)

    context = {
        'products': paginated_products,
        'total_products': total_products,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'club': club
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/products/viewProducts.html', context)

def extract_features(description):
    """Helper function to extract product features from description"""
    if description:
        return [
            "مصنوعة من مواد فائقة الجودة",
            "تصميم عصري وأنيق",
            "سهولة الاستخدام",
            "ضمان لمدة سنة"
        ]
    return []

def viewProductsSpecific(request, id):
    context = {}
    user = request.user
    club = user.userprofile.student_profile.club

    product = ProductsModel.objects.get(id=id)

    product.features = extract_features(product.desc)

    from datetime import timedelta
    from django.utils import timezone
    product.is_new = product.created_at >= timezone.now() - timedelta(days=7) if hasattr(product, 'created_at') else False

    related_products = ProductsModel.objects.filter(club=club,approval_status='approved').exclude(id=id)[:3]

    context = {
        'product': product,
        'products': related_products,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/products/viewSpecific.html', context)


def viewServices(request):
    context = {}
    user = request.user
    club = user.userprofile.student_profile.club

    # Get all active promotions for services in this club
    active_promotions = Promotion.objects.filter(
        status='active',
        promotion_type='service',
        service__club=club
    ).select_related('service')

    # Get promoted service IDs
    promoted_service_ids = active_promotions.values_list('service_id', flat=True)

    # Get approved services - promoted first
    services = ServicesModel.objects.filter(
        club=club,
        is_enabled=True,
        approval_status='approved'
    ).order_by('-creation_date')

    # Add promotion info to each service
    promoted_services = []
    regular_services = []

    for service in services:
        if service.id in promoted_service_ids:
            service.is_promoted = True
            promoted_services.append(service)
        else:
            service.is_promoted = False
            regular_services.append(service)

    # Combine lists with promoted first
    services = promoted_services + regular_services

    # Filter by featured/premium promotions if requested
    promotion_filter = request.GET.get('promotion')
    if promotion_filter in ['featured', 'premium']:
        promoted_services = active_promotions.filter(
            promotion_level=promotion_filter
        ).values_list('service_id', flat=True)
        services = services.filter(id__in=promoted_services)

    classifications = ProductsClassificationModel.objects.filter(club=club)

    if services:
        # Calculate average monthly price (normalized)
        avg_monthly_price = sum(service.monthly_price for service in services) / len(services)
        avg_monthly_price = round(avg_monthly_price, 1)

        # Calculate average total price
        avg_total_price = sum(service.discounted_price or service.price for service in services) / len(services)
        avg_total_price = round(avg_total_price, 1)

        avg_duration = sum(service.duration for service in services) / len(services)
        avg_duration_hours = int(avg_duration // 60)
        avg_duration_minutes = int(avg_duration % 60)

        # Get unique pricing periods for filtering
        pricing_periods = list(set(service.pricing_period_months for service in services))
        pricing_periods.sort()
    else:
        avg_monthly_price = 0
        avg_total_price = 0
        avg_duration_hours = 0
        avg_duration_minutes = 0
        pricing_periods = []

    context = {
        'services': services,
        'classifications': classifications,
        'avg_monthly_price': avg_monthly_price,
        'avg_total_price': avg_total_price,
        'avg_duration_hours': avg_duration_hours,
        'avg_duration_minutes': avg_duration_minutes,
        'pricing_periods': pricing_periods,
        'PRICING_PERIOD_CHOICES': ServicesModel.PRICING_PERIOD_CHOICES,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/services/viewServices.html', context)


def viewServicesSpecific(request, id):
    context = {}
    user = request.user
    club = user.userprofile.student_profile.club
    service = ServicesModel.objects.get(id=id)
    services = ServicesModel.objects.filter(club=club,approval_status='approved')
    order = ServiceOrderModel.objects.filter(service=service, student=user).order_by('-id').first()
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/services/viewSpecific.html', {'service':service, 'services':services, 'order':order})


def viewArticles(request):
    user = request.user
    club = user.userprofile.student_profile.club
    arts = Blog.objects.filter(club=club)
    featured_article = arts.order_by('-creation_date').first()

    context = {
        'arts': arts,
        'featured_article': featured_article,
        'club':club
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/blog/viewArticless.html', context)

def viewArticle(request,id):
    user = request.user
    club = user.userprofile.student_profile.club

    try:
        article = Blog.objects.get(id=id, club=club)

        related_articles = Blog.objects.filter(club=club).exclude(id=id)[:3]

        context = {
            'article': article,
            'related_articles': related_articles
        }
        context['LANGUAGE_CODE'] = translation.get_language()
        return render(request, 'student/blog/viewArticle.html', context)

    except Blog.DoesNotExist:
        return redirect('viewArticles')


def OrderService(request, service_id):
    student = request.user
    service = ServicesModel.objects.get(id=service_id)
    orders = ServiceOrderModel.objects.filter(service=service, student=student).order_by('-id')
    if orders.exists():
        if orders.first().has_subscription():
            return redirect('viewServicesSpecific', service_id)
    end_datetime = datetime.timedelta(days=30) + timezone.now()
    order = ServiceOrderModel.objects.create(service=service, student=student, price=service.price, is_complited=True, end_datetime=end_datetime, creation_date=timezone.now())
    order.save()
    return redirect('studentIndex')

def add_review(request):
    context = {}
    """Allows a student to review any coach in their club."""
    user = request.user

    # ✅ Ensure user has a valid StudentProfile
    student_profile = getattr(user.userprofile, 'student_profile', None)
    if not student_profile:
        messages.error(request, "❌ لم يتم العثور على ملف الطالب الخاص بك.")
        return redirect('studentIndex')

    club = student_profile.club
    if not club:
        messages.error(request, "❌ أنت غير مسجل في أي نادٍ.")
        return redirect('studentIndex')

    # ✅ Get all coaches in the club
    coaches = CoachProfile.objects.filter(club=club)

    if request.method == 'POST':
        selected_coach_id = request.POST.get('coach_id')

        if not selected_coach_id:
            messages.error(request, "❌ يرجى اختيار مدرب لإضافة تقييم.")
            return redirect('add_review')

        # ✅ Check if the coach exists
        coach_profile = get_object_or_404(CoachProfile, id=selected_coach_id)

        # ✅ Check if the student already reviewed this coach
        existing_review = Review.objects.filter(student=student_profile, coach=coach_profile).first()

        # ✅ Use form with instance for updating existing review
        form = ReviewForm(request.POST, instance=existing_review)

        if form.is_valid():
            review = form.save(commit=False)
            review.student = student_profile
            review.coach = coach_profile
            review.save()

            messages.success(request, "✅ تم إرسال التقييم بنجاح!")
            return redirect('view_reviews')
        else:
            messages.error(request, f"❌ حدث خطأ أثناء إرسال التقييم: {form.errors}")
    else:
        form = ReviewForm()
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/reviews/add_review.html', {
        'form': form,
        'coaches': coaches  # ✅ Correctly passing only relevant coaches
    })
    
def view_reviews(request):
    context = {}
    """Displays the reviews written by the logged-in student."""
    user = request.user

    # ✅ Ensure user has a valid UserProfile and StudentProfile
    try:
        student_profile = user.userprofile.student_profile
    except AttributeError:
        messages.error(request, "لم يتم العثور على ملف الطالب الخاص بك.")
        return redirect('studentIndex')

    # ✅ Fetch only the reviews this student wrote
    student_reviews = Review.objects.filter(student=student_profile).select_related('coach').order_by('-created_at')
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/reviews/view_reviews.html', {
        'student_reviews': student_reviews,
    })
      
def edit_review(request, review_id):
    context = {}
    """Allows a student to edit their existing review."""
    user = request.user
    review = get_object_or_404(Review, id=review_id, student=user.userprofile.student_profile)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تعديل التقييم بنجاح!")
            return redirect('view_reviews')
    else:
        form = ReviewForm(instance=review)
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/reviews/edit_review.html', {'form': form, 'review': review})

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

@login_required
def get_service_duration(request, service_id):
    try:
        service = ServicesModel.objects.get(id=service_id)
        return JsonResponse({'duration': service.duration})
    except ServicesModel.DoesNotExist:
        return JsonResponse({'duration': 0})


@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))

        # Get the product
        product = get_object_or_404(ProductsModel, id=product_id)

        # Check if stock is available
        if product.stock < quantity:
            return JsonResponse({
                'success': False,
                'message': 'لا يوجد مخزون كافي'
            })

        # Check if item already in cart
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )

        # If item already exists, update quantity
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        # Get cart count for navbar badge
        cart_count = CartItem.objects.filter(user=request.user).aggregate(
            total=Sum('quantity'))['total'] or 0

        return JsonResponse({
            'success': True,
            'message': 'تمت إضافة المنتج إلى السلة',
            'cart_count': cart_count
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def cart(request):
    context = {}
    product_items = CartItem.objects.filter(user=request.user)
    service_items = ServiceCartItem.objects.filter(user=request.user)

    product_total = sum(item.total_price for item in product_items)

    service_total = sum(item.total_price for item in service_items)
    original_service_total = 0
    total_service_savings = 0

    for item in service_items:
        original_item_total = item.quantity * item.service.price
        original_service_total += original_item_total

        if item.service.discounted_price and item.service.discounted_price != item.service.price:
            item_savings = original_item_total - item.total_price
            total_service_savings += item_savings

    total_price = product_total + service_total
    original_total_price = product_total + original_service_total
    total_savings = original_total_price - total_price if original_total_price != total_price else 0

    has_service_discounts = any(
        item.service.discounted_price and item.service.discounted_price != item.service.price
        for item in service_items
    )

    context = {
        'product_items': product_items,
        'service_items': service_items,
        'product_total': product_total,
        'service_total': service_total,
        'original_service_total': original_service_total if has_service_discounts else None,
        'total_service_savings': total_service_savings if total_service_savings > 0 else None,
        'total_price': total_price,
        'original_total_price': original_total_price if has_service_discounts else None,
        'total_savings': total_savings if total_savings > 0 else None,
        'has_service_discounts': has_service_discounts,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/cart/cart.html', context)

# Update Cart Quantity
@login_required
def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')

        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)

        if action == 'increase':
            if cart_item.quantity >= cart_item.product.stock:
                return JsonResponse({
                    'success': False,
                    'message': 'لا يوجد مخزون كافي'
                })

            cart_item.quantity += 1
            cart_item.save()

        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                # Delete ServiceCartItem before deleting CartItem
                ServiceCartItem.objects.filter(cart_item=cart_item).delete()
                cart_item.delete()

        elif action == 'remove':
            # Delete ServiceCartItem before deleting CartItem
            ServiceCartItem.objects.filter(cart_item=cart_item).delete()
            cart_item.delete()

        # Recalculate totals
        remaining_items = CartItem.objects.filter(user=request.user)
        total_price = sum(item.total_price for item in remaining_items)
        cart_count = remaining_items.aggregate(total=Sum('quantity'))['total'] or 0

        return JsonResponse({
            'success': True,
            'total_price': float(total_price),
            'cart_count': cart_count,
            'item_total': float(cart_item.total_price) if action != 'remove' else 0
        })

    return JsonResponse({'success': False})

@login_required
def delete_product_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('cart')

@login_required
def update_service_cart(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})

    item_id = request.POST.get('item_id')
    action = request.POST.get('action')

    if not item_id or not action:
        return JsonResponse({'success': False, 'message': 'Missing parameters'})

    try:
        cart_item = ServiceCartItem.objects.get(id=item_id, user=request.user)

        if action == 'remove':
            try:
                service_id = cart_item.service.id

                booking_services = BookingService.objects.filter(
                    service__id=service_id,
                    booking__student__user=request.user
                )

                for booking_service in booking_services:
                    booking = booking_service.booking
                    appointment = booking.appointment

                    booking_service.delete()
                    booking.delete()
                    appointment.delete()

            except Exception as e:
                print(f"Error removing appointments: {str(e)}")

            cart_item.delete()

            product_total = get_cart_product_total(request.user)
            service_total = get_cart_service_total(request.user)
            total_price = product_total + service_total
            cart_count = get_cart_count(request.user)

            return JsonResponse({
                'success': True,
                'item_total': 0,
                'total_price': total_price,
                'product_total': product_total,
                'service_total': service_total,
                'cart_count': cart_count,
                'message': 'تم حذف الخدمة والموعد المرتبط بها بنجاح'
            })

        elif action == 'increase':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

        product_total = get_cart_product_total(request.user)
        service_total = get_cart_service_total(request.user)
        total_price = product_total + service_total
        cart_count = get_cart_count(request.user)

        return JsonResponse({
            'success': True,
            'cart_item_quantity': cart_item.quantity if action != 'remove' else 0,
            'item_total': cart_item.total_price if action != 'remove' else 0,
            'total_price': total_price,
            'product_total': product_total,
            'service_total': service_total,
            'cart_count': cart_count
        })

    except ServiceCartItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# Helper functions
def get_cart_product_total(user):
    return CartItem.objects.filter(user=user).aggregate(
        total=Sum(F('quantity') * F('product__price')))['total'] or 0

def get_cart_service_total(user):
    return ServiceCartItem.objects.filter(user=user).aggregate(
        total=Sum(F('quantity') * F('service__price')))['total'] or 0

def get_cart_count(user):
    product_count = CartItem.objects.filter(user=user).aggregate(Sum('quantity'))['quantity__sum'] or 0
    service_count = ServiceCartItem.objects.filter(user=user).count()
    return product_count + service_count



def get_cart_count(request):
    if request.user.is_authenticated:
        product_count = CartItem.objects.filter(user=request.user).aggregate(
            total=Sum('quantity'))['total'] or 0
        service_count = ServiceCartItem.objects.filter(user=request.user).aggregate(
            total=Sum('quantity'))['total'] or 0
        total_count = product_count + service_count
        return JsonResponse({'cart_count': total_count})
    return JsonResponse({'cart_count': 0})


@login_required
def checkout(request):
    userprofile = UserProfile.objects.get(user=request.user)
    student = userprofile.student_profile
    product_items = CartItem.objects.filter(user=request.user)
    service_items = ServiceCartItem.objects.filter(user=request.user)

    if not product_items.exists() and not service_items.exists():
        messages.warning(request, 'سلة التسوق فارغة' if get_language() == 'ar' else 'Your cart is empty')
        return redirect('cart')

    out_of_stock_items = []
    for item in product_items:
        if item.quantity > item.product.stock:
            out_of_stock_items.append(item.product.title)

    if out_of_stock_items:
        messages.error(request,
                       f'المنتجات التالية غير متوفرة بالكمية المطلوبة: {", ".join(out_of_stock_items)}'
                       if get_language() == 'ar'
                       else f'These products are not available in the requested quantity: {", ".join(out_of_stock_items)}')
        return redirect('cart')

    # Calculate totals
    product_total = sum(item.total_price for item in product_items)
    service_total = sum(item.total_price for item in service_items)
    subtotal = product_total + service_total

    # Get applied coupon from session if exists
    applied_coupon = None
    discount_amount = Decimal(0)

    if 'applied_coupon' in request.session:
        try:
            applied_coupon = request.session['applied_coupon']
            coupon = Coupon.objects.get(id=applied_coupon['coupon_id'])

            # Validate coupon again in case it became invalid since being applied
            if coupon.is_valid(student=student):
                discount_amount = Decimal(str(applied_coupon['discount_amount']))
            else:
                # Remove invalid coupon from session
                del request.session['applied_coupon']
                messages.warning(request,
                                 'كوبون الخصم لم يعد صالحاً' if get_language() == 'ar'
                                 else 'The coupon is no longer valid')
        except Coupon.DoesNotExist:
            # Remove invalid coupon from session
            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']

    total_after_discount = subtotal - discount_amount

    context = {
        'product_items': product_items,
        'service_items': service_items,
        'product_total': product_total,
        'service_total': service_total,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'total_after_discount': total_after_discount,
        'applied_coupon': applied_coupon,
        'user': userprofile,
        'student': student,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/cart/checkout.html', context)

from coach_dashboard.models import CouponUsage
from accountant_dashboard.models import VATSettings


@login_required
def place_order(request):
    print("=== place_order called ===")
    club = get_user_club(request.user)
    print(f"User: {request.user}, Club: {club}")

    context = {}
    if request.method == 'POST':
        print("--- POST request received ---")

        product_items = CartItem.objects.filter(user=request.user)
        service_items = ServiceCartItem.objects.filter(user=request.user)

        print(f"Product items count: {product_items.count()}")
        print(f"Service items count: {service_items.count()}")

        if not product_items.exists() and not service_items.exists():
            print("Cart is empty!")
            messages.warning(request, 'سلة التسوق فارغة' if get_language() == 'ar' else 'Your cart is empty')
            return redirect('cart')

        lang = get_language()
        print(f"Language: {lang}")
        currency_symbol = 'ر.س' if lang == 'ar' else 'SAR'

        # Capture form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        region = request.POST.get('region')
        postal_code = request.POST.get('postal_code')
        notes = request.POST.get('notes', '')
        payment_method = request.POST.get('payment_method', 'credit_card')

        print(f"Payment method: {payment_method}")
        print(f"Customer: {first_name} {last_name}, Email: {email}, Phone: {phone}")

        # Validate stock
        for item in product_items:
            print(
                f"Checking stock for product {item.product.title}: requested {item.quantity}, available {item.product.stock}")
            if item.quantity > item.product.stock:
                msg = f"المنتج {item.product.title} غير متوفر بالكمية المطلوبة" if lang == 'ar' else f"The product {item.product.title} is not available in the requested quantity"
                messages.error(request, msg)
                return redirect('cart')

        # Cash on delivery branch
        if payment_method == 'cash_on_delivery':
            print("Payment method is cash on delivery — storing order in session")
            request.session['pending_order'] = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'address': address,
                'city': city,
                'region': region,
                'postal_code': postal_code,
                'notes': notes,
                'payment_method': payment_method,
                'product_items': [
                    {
                        'product_id': item.product.id,
                        'quantity': item.quantity,
                        'price': float(item.product.price)
                    } for item in product_items
                ],
                'service_items': [
                    {
                        'service_id': item.service.id,
                        'quantity': item.quantity,
                        'price': float(item.service.price)
                    } for item in service_items
                ]
            }

            product_total = sum(item.total_price for item in product_items)
            service_total = sum(item.total_price for item in service_items)
            total_price = product_total + service_total

            request.session['order_total'] = float(total_price)
            print(f"Stored order total: {total_price}")
            return redirect('bank_transfer_info')

        print("Continuing with credit card payment logic")
        product_total = sum(item.total_price for item in product_items)
        service_total = sum(item.total_price for item in service_items)
        total_price = product_total + service_total
        print(f"Product total: {product_total}, Service total: {service_total}, Grand total: {total_price}")

        club = None
        if product_items.exists():
            club = product_items.first().product.club
        elif service_items.exists():
            club = service_items.first().service.club
        print(f"Club determined for order: {club}")

        try:
            with transaction.atomic():
                applied_coupon = request.session.get('applied_coupon')
                coupon = None
                coupon_discount = Decimal(0)

                if applied_coupon:
                    coupon = Coupon.objects.get(id=applied_coupon['coupon_id'])
                    coupon_discount = Decimal(str(applied_coupon['discount_amount']))
                    print(f"Coupon applied: {coupon.code}, Discount: {coupon_discount}")

                subtotal = product_total + service_total
                total_with_discount = subtotal - coupon_discount
                print(f"Subtotal: {subtotal}, Discount: {coupon_discount}, Total after discount: {total_with_discount}")

                order = Order.objects.create(
                    user=request.user,
                    club=club,
                    subtotal=subtotal,
                    discount_amount=coupon_discount,
                    total_price=total_with_discount,
                    status='confirmed' if payment_method == 'credit_card' else 'pending',
                    payment_method=payment_method,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    address=address,
                    city=city,
                    region=region,
                    postal_code=postal_code,
                    notes=notes
                )
                print(f"Order created: ID={order.id}")

                if coupon:
                    CouponUsage.objects.create(
                        coupon=coupon,
                        student=request.user.userprofile.student_profile,
                        order=order,
                        discount_amount=coupon_discount
                    )
                    coupon.times_used += 1
                    coupon.save()
                    print("Coupon usage recorded and updated")

                    if 'applied_coupon' in request.session:
                        del request.session['applied_coupon']
                        print("Coupon removed from session")

                # Order items
                has_products = product_items.exists()
                has_services = service_items.exists()
                print(f"Has products: {has_products}, Has services: {has_services}")

                for item in product_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price
                    )
                    print(f"Product added to order: {item.product.title} x {item.quantity}")
                    item.product.stock -= item.quantity
                    item.product.save()

                if has_services:
                    print("Processing service items...")
                    try:
                        for item in service_items:
                            OrderItem.objects.create(
                                order=order,
                                service=item.service,
                                quantity=item.quantity,
                                price=item.service.price
                            )
                            print(f"Service added to order: {item.service.title} x {item.quantity}")
                    except Exception as e:
                        print(f"Error in service processing: {e}")

                # Clear cart
                product_items.delete()
                service_items.delete()
                print("Cart cleared after order creation")

                if has_products and has_services:
                    msg = 'تم إتمام عملية شراء المنتجات والخدمات بنجاح' if lang == 'ar' else 'Product and service purchase completed successfully.'
                elif has_products:
                    msg = 'تم إتمام عملية شراء المنتجات بنجاح' if lang == 'ar' else 'Product purchase completed successfully.'
                else:
                    msg = 'تم إتمام عملية شراء الخدمات بنجاح' if lang == 'ar' else 'Service purchase completed successfully.'

                for item in order.items.all():
                    print(f"Notifying coach for order item ID: {item.id}")
                    notify_coach_for_order(item)

                messages.success(request, msg)
                print("Order completed successfully")
                return redirect('order_details', order_id=order.id)

        except Exception as e:
            print(f"Exception occurred: {e}")
            messages.error(request,
                           f"حدث خطأ أثناء معالجة الطلب: {str(e)}" if lang == 'ar' else f"Error processing order: {str(e)}")
            return redirect('checkout')

    print("Request method was not POST — redirecting to checkout")
    context['LANGUAGE_CODE'] = translation.get_language()
    return redirect('checkout')


from coach_dashboard.views import notify_coach_for_refund,notify_coach_for_order,notify_coach_for_review
from decimal import Decimal
from students.models import ServicesModel
from students.models import ProductsModel
@login_required
def confirm_order(request):
    club = get_user_club(request.user)
    print("DEBUG: Entered confirm_order view")
    print("DEBUG: Request method:", request.method)

    if request.method != 'POST':
        print("DEBUG: Not a POST request. Redirecting to checkout.")
        return redirect('checkout')

    pending_order_data = request.session.get('pending_order')
    print("DEBUG: Session keys:", request.session.keys())
    print("DEBUG: pending_order_data:", pending_order_data)

    if not pending_order_data:
        messages.error(request, 'لا توجد بيانات طلب معلقة' if get_language() == 'ar' else 'No pending order data found')
        return redirect('checkout')

    lang = get_language()
    currency_symbol = 'ر.س' if lang == 'ar' else 'SAR'

    try:
        with transaction.atomic():
            print("DEBUG: Starting transaction for order creation")

            product_items_data = pending_order_data.get('product_items', [])
            service_items_data = pending_order_data.get('service_items', [])

            print("DEBUG: Product items:", product_items_data)
            print("DEBUG: Service items:", service_items_data)

            product_total = sum(item['price'] * item['quantity'] for item in product_items_data)
            service_total = sum(item['price'] * item['quantity'] for item in service_items_data)
            total_price = product_total + service_total
            print("DEBUG: Total price before VAT:", total_price)

            total_price = Decimal(str(total_price))

            total_with_tax = total_price
            print("DEBUG: Total with tax:", total_with_tax)

            # Determine club again from products/services
            club = None
            if product_items_data:
                product = ProductsModel.objects.get(id=product_items_data[0]['product_id'])
                club = product.club
                print("DEBUG: Club from product:", club)
            elif service_items_data:
                service = ServicesModel.objects.get(id=service_items_data[0]['service_id'])
                club = service.club
                print("DEBUG: Club from service:", club)

            transfer_receipt = request.FILES.get('transfer_receipt')
            print("DEBUG: Transfer receipt uploaded:", bool(transfer_receipt))

            order = Order.objects.create(
                user=request.user,
                club=club,
                total_price=total_with_tax,
                subtotal =total_price,
                status='pending',
                payment_method='cash_on_delivery',
                first_name=pending_order_data['first_name'],
                last_name=pending_order_data['last_name'],
                email=pending_order_data['email'],
                phone=pending_order_data['phone'],
                address=pending_order_data['address'],
                city=pending_order_data['city'],
                region=pending_order_data['region'],
                postal_code=pending_order_data['postal_code'],
                notes=pending_order_data['notes'],
                transfer_receipt=transfer_receipt,
                transfer_uploaded_at=timezone.now() if transfer_receipt else None
            )
            print("DEBUG: Order created with ID:", order.id)

            for item_data in product_items_data:
                product = ProductsModel.objects.get(id=item_data['product_id'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item_data['quantity'],
                    price=product.price
                )
                print(f"DEBUG: Added product item {product.title} x {item_data['quantity']}")

            for item_data in service_items_data:
                service = ServicesModel.objects.get(id=item_data['service_id'])
                OrderItem.objects.create(
                    order=order,
                    service=service,
                    quantity=item_data['quantity'],
                    price=service.price
                )
                print(f"DEBUG: Added service item {service.title} x {item_data['quantity']}")

            if club:
                customer_name = f"{pending_order_data['first_name']} {pending_order_data['last_name']}"
                receipt_status = "تم رفع إثبات التحويل - يحتاج مراجعة" if transfer_receipt else "في انتظار رفع إثبات التحويل"
                receipt_status_en = "Bank transfer receipt uploaded - needs review" if transfer_receipt else "Waiting for transfer receipt upload"

                if product_items_data and service_items_data:
                    msg = f"طلب منتجات وخدمات جديد رقم #{order.id} بقيمة {total_with_tax} {currency_symbol} من العميل {customer_name}. {receipt_status}" if lang == 'ar' else f"New product & service order #{order.id} worth {total_with_tax} {currency_symbol} from {customer_name}. {receipt_status_en}"
                elif product_items_data:
                    msg = f"طلب منتجات جديد رقم #{order.id} بقيمة {total_with_tax} {currency_symbol} من العميل {customer_name}. {receipt_status}" if lang == 'ar' else f"New product order #{order.id} worth {total_with_tax} {currency_symbol} from {customer_name}. {receipt_status_en}"
                else:
                    msg = f"طلب خدمات جديد رقم #{order.id} بقيمة {total_with_tax} {currency_symbol} من العميل {customer_name}. {receipt_status}" if lang == 'ar' else f"New service order #{order.id} worth {total_with_tax} {currency_symbol} from {customer_name}. {receipt_status_en}"

                Notification.objects.create(club=club, message=msg, is_read=False, created_at=timezone.now())
                print("DEBUG: Notification created for club")

            CartItem.objects.filter(user=request.user).delete()
            ServiceCartItem.objects.filter(user=request.user).delete()
            print("DEBUG: Cleared cart items")

            if 'pending_order' in request.session:
                del request.session['pending_order']
                print("DEBUG: Deleted pending_order from session")
            if 'order_total' in request.session:
                del request.session['order_total']
                print("DEBUG: Deleted order_total from session")

            success_msg = 'تم إنشاء الطلب بنجاح'
            if transfer_receipt:
                success_msg += ' وتم رفع إثبات التحويل. سيتم مراجعة طلبك وتأكيده قريباً.'
            else:
                success_msg += '. يمكنك رفع إثبات التحويل من صفحة تفاصيل الطلب.'

            if lang == 'en':
                success_msg = 'Order created successfully'
                if transfer_receipt:
                    success_msg += ' and transfer receipt uploaded. Your order will be reviewed and confirmed soon.'
                else:
                    success_msg += '. You can upload the transfer receipt from the order details page.'

            messages.success(request, success_msg)
            print("DEBUG: Success message sent")
            return redirect('order_details', order_id=order.id)

    except Exception as e:
        print("DEBUG: Exception occurred:", str(e))
        messages.error(request, f"حدث خطأ أثناء معالجة الطلب: {str(e)}" if lang == 'ar' else f"Error processing order: {str(e)}")
        return redirect('checkout')



def process_order_confirmation(order):
    """
    Process order confirmation - update stock and subscriptions
    This should be called when an order status changes from 'pending' to 'confirmed'
    """
    try:
        with transaction.atomic():
            # Process product items - reduce stock
            product_items = order.items.filter(product__isnull=False)
            for item in product_items:
                product = item.product
                if product.stock >= item.quantity:
                    product.stock -= item.quantity
                    product.save()
                else:
                    raise ValueError(f"Insufficient stock for product {product.title}")

            # Process service items - update subscriptions
            service_items = order.items.filter(service__isnull=False)
            for item in service_items:
                service = item.service

                # Handle service subscriptions
                existing_service_order = ServiceOrderModel.objects.filter(
                    student=order.user,
                    service=service,
                    order__status='confirmed'
                ).order_by('-end_datetime').first()

                if existing_service_order:
                    # Calculate subscription extension based on pricing_period_months
                    subscription_months = service.pricing_period_months * item.quantity

                    if existing_service_order.end_datetime > timezone.now():
                        new_end_datetime = existing_service_order.end_datetime + timezone.timedelta(days=subscription_months * 30)
                    else:
                        new_end_datetime = timezone.now() + timezone.timedelta(days=subscription_months * 30)

                    existing_service_order.end_datetime = new_end_datetime
                    existing_service_order.price += service.price * item.quantity
                    existing_service_order.creation_date = timezone.now()
                    existing_service_order.is_complited = False
                    existing_service_order.save()
                else:
                    # Create new service subscription using pricing_period_months
                    subscription_months = service.pricing_period_months * item.quantity

                    ServiceOrderModel.objects.create(
                        service=service,
                        student=order.user,
                        price=service.price * item.quantity,
                        is_complited=False,
                        end_datetime=timezone.now() + timezone.timedelta(days=subscription_months * 30),
                        creation_date=timezone.now()
                    )

                # Handle appointment payments
                bookings = BookingService.objects.filter(
                    service=service,
                ).select_related('booking', 'booking__appointment')

                for booking_service in bookings:
                    try:
                        if (booking_service.booking and
                                hasattr(booking_service.booking, 'appointment') and
                                booking_service.booking.appointment):

                            appointment = booking_service.booking.appointment
                            appointment.is_paid = True
                            appointment.save()
                    except SalonAppointment.DoesNotExist:
                        logger.error(f"Appointment not found for booking: {booking_service.booking.id}")
                        continue

            return True

    except Exception as e:
        logger.error(f"Error processing order confirmation: {str(e)}")
        return False

def check_service_subscription_status(user, service):
    """
    Check if user has an active subscription for a service through confirmed orders
    """
    confirmed_orders = Order.objects.filter(
        user=user,
        status='confirmed',
        items__service=service
    )

    if not confirmed_orders.exists():
        return {
            'has_subscription': False,
            'message': 'No confirmed orders found for this service'
        }

    # Check if there's an active ServiceOrderModel
    active_subscription = ServiceOrderModel.objects.filter(
        student=user,
        service=service,
        end_datetime__gt=timezone.now(),
        is_complited=False
    ).first()

    return {
        'has_subscription': bool(active_subscription),
        'subscription': active_subscription,
        'confirmed_orders_count': confirmed_orders.count()
    }


def prevent_duplicate_service_processing(order):
    """
    Prevent processing the same service multiple times if order is confirmed again
    You might want to add a processed flag to OrderItem or track processed items
    """
    # Add a field to OrderItem model: is_processed = models.BooleanField(default=False)

    service_items = order.items.filter(
        service__isnull=False,
        is_processed=False  # Only process unprocessed items
    )

    for item in service_items:
        # Your processing logic here
        # ...

        # Mark as processed
        item.is_processed = True
        item.save()


def process_order_cancellation(order):
    """
    Process order cancellation - restore stock if needed
    This should be called when an order is cancelled
    """
    try:
        with transaction.atomic():
            # For cancelled orders, we don't need to restore stock since it was never reduced
            # But we might want to log the cancellation or send notifications

            # Create notification for customer
            lang = 'ar'  # You might want to get this from user preferences
            msg = f"تم إلغاء طلبك رقم #{order.id}" if lang == 'ar' else f"Your order #{order.id} has been cancelled"

            # You might want to create a notification system for customers
            # For now, we'll just log it
            logger.info(f"Order {order.id} cancelled for user {order.user.username}")

            return True

    except Exception as e:
        logger.error(f"Error processing order cancellation: {str(e)}")
        return False


# This function should be called whenever an order status changes
def handle_order_status_change(order, old_status, new_status):
    """
    Handle order status changes
    """
    if old_status == 'pending' and new_status == 'confirmed':
        # Order confirmed - process the order
        success = process_order_confirmation(order)
        if not success:
            # Rollback status change if processing failed
            order.status = old_status
            order.save()
            return False

    elif new_status == 'cancelled':
        # Order cancelled
        process_order_cancellation(order)

    return True


@login_required
def bank_transfer_info(request):
    """
    Display bank transfer information and handle the form to proceed with order creation
    """
    user = request.user
    club = get_user_club(user)
    # Check if there's pending order data
    if 'pending_order' not in request.session:
        messages.error(request, 'لا توجد بيانات طلب معلقة' if get_language() == 'ar' else 'No pending order data found')
        return redirect('checkout')

    context = {
        'order_total': request.session.get('order_total', 0),
        'pending_order': request.session.get('pending_order', {}),
        'club': club,
    }

    return render(request, 'student/orders/bank_transfer_info.html', context)


@login_required
def upload_transfer_receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    lang = get_language()

    if request.method == 'POST':
        transfer_receipt = request.FILES.get('transfer_receipt')

        if transfer_receipt:
            order.transfer_receipt = transfer_receipt
            order.transfer_uploaded_at = timezone.now()
            order.status = 'pending'  # Change status to pending for club review
            order.save()

            # Create notification for club
            customer_name = f"{order.first_name} {order.last_name}"
            has_products = order.items.filter(product__isnull=False).exists()
            has_services = order.items.filter(service__isnull=False).exists()

            if has_products and has_services:
                msg = f"طلب منتجات وخدمات جديد رقم #{order.id} بقيمة {order.total_price} ر.س من العميل {customer_name}. تم رفع إثبات التحويل البنكي - يحتاج مراجعة" if lang == 'ar' else f"New product & service order #{order.id} worth {order.total_price} SAR from {customer_name}. Bank transfer receipt uploaded - needs review"
            elif has_products:
                msg = f"طلب منتجات جديد رقم #{order.id} بقيمة {order.total_price} ر.س من العميل {customer_name}. تم رفع إثبات التحويل البنكي - يحتاج مراجعة" if lang == 'ar' else f"New product order #{order.id} worth {order.total_price} SAR from {customer_name}. Bank transfer receipt uploaded - needs review"
            else:
                msg = f"طلب خدمات جديد رقم #{order.id} بقيمة {order.total_price} ر.س من العميل {customer_name}. تم رفع إثبات التحويل البنكي - يحتاج مراجعة" if lang == 'ar' else f"New service order #{order.id} worth {order.total_price} SAR from {customer_name}. Bank transfer receipt uploaded - needs review"

            Notification.objects.create(
                club=order.club,
                message=msg,
                is_read=False,
                created_at=timezone.now()
            )

            messages.success(request, 'تم رفع إثبات التحويل بنجاح. سيتم مراجعة طلبك وتأكيده قريباً.' if lang == 'ar' else 'Transfer receipt uploaded successfully. Your order will be reviewed and confirmed soon.')
            return redirect('order_details', order_id=order.id)
        else:
            messages.error(request, 'يرجى اختيار صورة إثبات التحويل' if lang == 'ar' else 'Please select a transfer receipt image')

    return redirect('bank_transfer_info', order_id=order.id)


@login_required
def add_service_to_cart(request):
    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        quantity = int(request.POST.get('quantity', 1))
        action = request.POST.get('action', 'add')  # New parameter to handle confirmation

        if not service_id:
            return JsonResponse({'success': False, 'message': 'Service ID is required'})

        service = get_object_or_404(ServicesModel, id=service_id)
        user_profile = request.user.userprofile
        student = user_profile.student_profile

        # Check if student already has an active subscription for this service
        now = timezone.now()
        active_subscription = ServiceOrderModel.objects.filter(
            student=request.user,
            service=service,
            end_datetime__gte=now  # Subscription hasn't expired yet
        ).exists()

        if active_subscription and action != 'confirm_renewal':
            # Return a JSON response to show confirmation modal
            return JsonResponse({
                'success': False,
                'needs_confirmation': True,
                'message': 'لديك اشتراك نشط بالفعل في هذه الخدمة. هل ترغب في تجديد الاشتراك لشهر آخر؟',
                'service_id': service_id
            })

        # If we get here, either there's no active subscription or user confirmed renewal
        cart_item, created = ServiceCartItem.objects.get_or_create(
            user=request.user,
            service=service,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        messages.success(request, 'تمت إضافة الخدمة إلى السلة')
        return JsonResponse({'success': True, 'message': 'تمت إضافة الخدمة إلى السلة'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def update_service_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')

        cart_item = get_object_or_404(ServiceCartItem, id=item_id, user=request.user)

        if action == 'increase':
            cart_item.quantity += 1
            cart_item.save()

        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

        elif action == 'remove':
            cart_item.delete()

        remaining_service_items = ServiceCartItem.objects.filter(user=request.user)
        remaining_product_items = CartItem.objects.filter(user=request.user)

        service_total = sum(item.total_price for item in remaining_service_items)
        product_total = sum(item.total_price for item in remaining_product_items)
        total_price = service_total + product_total

        service_count = remaining_service_items.aggregate(total=Sum('quantity'))['total'] or 0
        product_count = remaining_product_items.aggregate(total=Sum('quantity'))['total'] or 0
        cart_count = service_count + product_count

        return JsonResponse({
            'success': True,
            'total_price': float(total_price),
            'cart_count': cart_count,
            'item_total': float(cart_item.total_price) if action != 'remove' else 0
        })

    return JsonResponse({'success': False})

@login_required
def view_student_profile(request):
    try:
        user_profile = request.user.userprofile
        student = user_profile.student_profile

        if not student:
            return render(request, 'error_page.html', {'message': 'No student profile found for this user.'})

        context = {
            'student': student,
            'userprofile': user_profile,
        }
        context['LANGUAGE_CODE'] = translation.get_language()
        return render(request, 'accounts/profiles/Student/ViewStudentProfile.html', context)

    except UserProfile.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'User profile not found.'})
@login_required
def view_student_profile(request):
    try:
        user_profile = request.user.userprofile
        student = user_profile.student_profile

        if not student:
            return render(request, 'error_page.html', {'message': 'No student profile found for this user.'})

        context = {
            'student': student,
            'userprofile': user_profile,
        }

        return render(request, 'accounts/profiles/Student/ViewStudentProfile.html', context)

    except UserProfile.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'User profile not found.'})

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['full_name', 'phone', 'birthday', 'about']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'phone': forms.TextInput(attrs={'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'birthday': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'about': forms.Textarea(attrs={'rows': 4, 'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'})
        }

@login_required
def edit_student_profile(request):
    try:
        user_profile = request.user.userprofile
        student = user_profile.student_profile

        if not student:
            return render(request, 'error_page.html', {'message': 'No student profile found for this user.'})

        if request.method == 'POST':
            form = StudentProfileForm(request.POST, instance=student)

            if form.is_valid():
                form.save()

                if 'profile_image_base64' in request.FILES:
                    image_file = request.FILES['profile_image_base64']
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    user_profile.profile_image_base64 = f"data:image/{image_file.content_type.split('/')[-1]};base64,{encoded_string}"
                    user_profile.save()

                return redirect('student_profile')
        else:
            form = StudentProfileForm(instance=student)

        context = {
            'form': form,
            'student': student,
            'user_profile': user_profile,
        }
        context['LANGUAGE_CODE'] = translation.get_language()
        return render(request, 'accounts/settings/Student/EditStudentProfile.html', context)

    except UserProfile.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'User profile not found.'})


@login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)

    cancellation = None
    if order.status == 'cancelled':
        try:
            cancellation = OrderCancellation.objects.get(order=order)
        except OrderCancellation.DoesNotExist:
            pass

    context = {
        'order': order,
        'order_items': order_items,
        'cancellation': cancellation,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/orders/order_details.html', context)

@login_required
def student_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'orders': orders
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/orders/student_orders.html', context)


from .forms import RefundDisputeForm
from club_dashboard.models import RefundDisputeAttachment
from django.utils.translation import gettext as _
from club_dashboard.models import RefundStatus


# students/views.py

@login_required
def create_refund_dispute(request, order_item_id):
    order_item = get_object_or_404(OrderItem, id=order_item_id, order__user=request.user)

    if request.method == 'POST':
        form = RefundDisputeForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            dispute = form.save(commit=False)
            dispute.status = RefundStatus.PENDING
            dispute.order_item = order_item
            dispute.deal = order_item.order
            dispute.client = request.user

            # Set vendor based on product/service creator
            if order_item.product:
                dispute.vendor = order_item.product.creator
            elif order_item.service:
                dispute.vendor = order_item.service.creator

            # Set original amount
            dispute.original_amount = order_item.price * order_item.quantity
            dispute.save()

            messages.success(request, _('Refund dispute created successfully.'))
            notify_coach_for_refund(dispute)
            return redirect('clientdetail', dispute_id=dispute.id)
    else:
        form = RefundDisputeForm(user=request.user)

    return render(request, 'student/refunds/create.html', {
        'form': form,
        'order_item': order_item,
        'title': _('Create Refund Dispute')
    })


@login_required
def edit_refund_dispute(request, dispute_id):
    """Edit an existing refund dispute"""
    dispute = get_object_or_404(RefundDispute, id=dispute_id)

    # Check permissions
    if not (request.user.is_staff or request.user == dispute.client):
        return HttpResponseForbidden("You don't have permission to edit this dispute.")

    if request.method == 'POST':
        form = RefundDisputeForm(request.POST, instance=dispute, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dispute updated successfully.')
            return redirect('refunds:detail', dispute_id=dispute.id)
    else:
        form = RefundDisputeForm(instance=dispute, user=request.user)

    return render(request, 'student/refunds/edit.html', {
        'form': form,
        'dispute': dispute
    })


from club_dashboard.forms import RefundAttachmentForm
@login_required
def dispute_attachments(request, dispute_id):
    """Manage dispute attachments"""
    dispute = get_object_or_404(RefundDispute, id=dispute_id)

    # Check permissions
    if not (request.user.is_staff or request.user == dispute.client or request.user == dispute.vendor):
        return HttpResponseForbidden("You don't have permission to view this dispute.")

    if request.method == 'POST':
        form = RefundAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.refund_dispute = dispute
            attachment.uploaded_by = request.user
            attachment.save()

            messages.success(request, 'Attachment uploaded successfully.')
            return redirect('attachments', dispute_id=dispute.id)
    else:
        form = RefundAttachmentForm()

    attachments = dispute.attachments.all().order_by('-created_at')

    return render(request, 'student/refunds/attachments.html', {
        'dispute': dispute,
        'attachments': attachments,
        'form': form
    })

from club_dashboard.models import RefundDispute
from django.http import HttpResponseForbidden
@login_required
def dispute_timeline(request, dispute_id):
    """Show dispute timeline/history"""
    dispute = get_object_or_404(RefundDispute, id=dispute_id)

    # Check permissions
    if not (request.user.is_staff or request.user == dispute.client or request.user == dispute.vendor):
        return HttpResponseForbidden("You don't have permission to view this dispute.")

    # Create timeline events
    timeline = []

    # Created event
    timeline.append({
        'date': dispute.created_at,
        'event': 'Dispute Created',
        'description': f'Dispute created by {dispute.client.get_full_name()}',
        'user': dispute.client,
        'type': 'created'
    })

    # Status change events
    if dispute.approved_at:
        timeline.append({
            'date': dispute.approved_at,
            'event': 'Dispute Approved',
            'description': f'Approved by {dispute.reviewed_by.get_full_name() if dispute.reviewed_by else "System"}',
            'user': dispute.reviewed_by,
            'type': 'approved'
        })

    if dispute.rejected_at:
        timeline.append({
            'date': dispute.rejected_at,
            'event': 'Dispute Rejected',
            'description': f'Rejected by {dispute.reviewed_by.get_full_name() if dispute.reviewed_by else "System"}',
            'user': dispute.reviewed_by,
            'type': 'rejected'
        })

    if dispute.resolved_at:
        timeline.append({
            'date': dispute.resolved_at,
            'event': 'Dispute Resolved',
            'description': 'Dispute marked as resolved',
            'user': dispute.reviewed_by,
            'type': 'resolved'
        })

    # Attachment events
    for attachment in dispute.attachments.all():
        timeline.append({
            'date': attachment.created_at,
            'event': 'Attachment Added',
            'description': f'File uploaded: {attachment.description or attachment.file.name}',
            'user': attachment.uploaded_by,
            'type': 'attachment'
        })

    # Sort timeline by date
    timeline.sort(key=lambda x: x['date'], reverse=True)

    return render(request, 'student/refunds/timeline.html', {
        'dispute': dispute,
        'timeline': timeline
    })


# Helper function
def get_vendor_from_order(order):
    """Get vendor from order - you'll need to implement this based on your Order model"""
    # This is a placeholder - implement based on your actual Order structure
    try:
        # If order has items with products that have creators
        for item in order.items.filter(product__isnull=False):
            if (item.product.creator and
                    hasattr(item.product.creator, 'userprofile') and
                    hasattr(item.product.creator.userprofile, 'Coach_profile')):
                return item.product.creator
        return None
    except Exception:
        return None


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from club_dashboard.models import RefundDispute
from club_dashboard.forms import RefundFilterForm

@login_required
def refund_dispute_list(request):
    """
    View for listing all refund disputes with filtering capabilities
    """
    # Get all disputes the user has access to
    if request.user.is_staff:
        disputes = RefundDispute.objects.all().order_by('-created_at')
    else:
        disputes = RefundDispute.objects.filter(
            models.Q(client=request.user) | models.Q(vendor=request.user)
        ).order_by('-created_at')

    # Initialize filter form
    filter_form = RefundFilterForm(request.GET or None)

    # Apply filters
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        dispute_type = filter_form.cleaned_data.get('dispute_type')
        priority = filter_form.cleaned_data.get('priority')
        refund_type = filter_form.cleaned_data.get('refund_type')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        search = filter_form.cleaned_data.get('search')
        amount_min = filter_form.cleaned_data.get('amount_min')
        amount_max = filter_form.cleaned_data.get('amount_max')

        if status:
            disputes = disputes.filter(status=status)
        if dispute_type:
            disputes = disputes.filter(dispute_type=dispute_type)
        if priority:
            disputes = disputes.filter(priority=priority)
        if refund_type:
            disputes = disputes.filter(refund_type=refund_type)
        if date_from:
            disputes = disputes.filter(created_at__gte=date_from)
        if date_to:
            disputes = disputes.filter(created_at__lte=date_to)
        if amount_min:
            disputes = disputes.filter(requested_refund_amount__gte=amount_min)
        if amount_max:
            disputes = disputes.filter(requested_refund_amount__lte=amount_max)
        if search:
            disputes = disputes.filter(
                models.Q(title__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(deal__id__icontains=search) |
                models.Q(client__email__icontains=search) |
                models.Q(vendor__email__icontains=search)
            )

    # Pagination
    paginator = Paginator(disputes, 10)  # Show 10 disputes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'disputes': page_obj,
        'filter_form': filter_form,
        'page_obj': page_obj,  # For pagination controls
    }
    return render(request, 'student/refunds/list.html', context)


from club_dashboard.models import RefundDisputeMessage
from django.core.files.storage import default_storage
from django.utils import timezone, translation
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
@login_required
def refund_dispute_detail(request, dispute_id):
    """
    View for displaying details of a specific refund dispute with chat functionality
    """
    dispute = get_object_or_404(RefundDispute, id=dispute_id)

    # Check permissions - only staff, client or vendor can view
    if not (request.user.is_staff or
            request.user == dispute.client or
            request.user == dispute.vendor):
        return HttpResponseForbidden("You don't have permission to view this dispute.")

    # Check for automatic escalation
    dispute.check_for_escalation()

    if request.method == 'POST':
        message = request.POST.get('message')
        attachments = request.FILES.getlist('attachments')

        if message:
            # Create the message
            msg = RefundDisputeMessage.objects.create(
                dispute=dispute,
                sender=request.user.userprofile,
                message=message
            )

            # Handle attachments
            if attachments:
                attachment_list = []
                for attachment in attachments:
                    # Save the file and create attachment record
                    file_name = default_storage.save(f'refund_attachments/{attachment.name}', attachment)
                    attachment_list.append({
                        'name': attachment.name,
                        'url': default_storage.url(file_name),
                        'type': attachment.content_type
                    })

                msg.attachments = attachment_list
                msg.save()

            # Update last message time
            dispute.last_message_time = timezone.now()
            dispute.save()

            messages.success(request, _('Message sent successfully'))
            return redirect('clientdetail', dispute_id=dispute.id)

    # Get all messages in chronological order
    conversation = dispute.messages.all().order_by('created_at')

    # Calculate time remaining for current stage
    time_remaining = None
    if dispute.next_escalation_time:
        time_remaining = dispute.next_escalation_time - timezone.now()

    context = {
        'dispute': dispute,
        'conversation': conversation,
        'time_remaining': time_remaining,
        'can_message': dispute.current_stage != 'resolved',
        'title': dispute.title,
        'LANGUAGE_CODE': translation.get_language(),
    }

    return render(request, 'student/refunds/detail.html', context)


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Review, Order, OrderItem
from .forms import ReviewForm


@login_required
def create_review(request, order_item_id):
    print("Entering create_review view...")
    print(f"Order item ID from URL: {order_item_id}")

    order_item = get_object_or_404(OrderItem, id=order_item_id, order__user=request.user)
    print(f"OrderItem found: {order_item}")

    try:
        student_profile = request.user.userprofile.student_profile
        print(f"Student profile retrieved: {student_profile}")
    except Exception as e:
        print(f"Error retrieving student profile: {e}")
        student_profile = None

    # Check if the student already reviewed this item
    existing_review = Review.objects.filter(
        student=student_profile,
        order_item=order_item
    ).first()
    print(f"Existing review: {existing_review}")

    if request.method == 'POST':
        print("Handling POST request...")
        # Pass order_item to the form
        form = ReviewForm(request.POST, instance=existing_review, order_item=order_item)
        print(f"Form valid: {form.is_valid()}")

        if form.is_valid():
            review = form.save(commit=False)
            review.student = student_profile
            review.order = order_item.order
            review.order_item = order_item

            # The form's save method will handle setting product/service
            review.save()
            print("Review saved successfully!")
            messages.success(request, 'Your review has been submitted successfully!')
            notify_coach_for_review(review)
            return redirect('order_details', order_id=order_item.order.id)
        else:
            print("Form errors:", form.errors)
    else:
        print("Handling GET request...")
        # Pass order_item to the form for GET requests too
        form = ReviewForm(instance=existing_review, order_item=order_item)

    context = {
        'form': form,
        'order_item': order_item,
        'existing_review': existing_review,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    print("Rendering template with context:", context)
    return render(request, 'student/reviews/create_review.html', context)


@login_required
def my_reviews(request):
    student = request.user.userprofile.student_profile
    reviews = Review.objects.filter(student=student).select_related('product', 'service')

    context = {
        'reviews': reviews,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'student/reviews/my_reviews.html', context)


from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import ProductClick, ServiceClick


@require_POST
@csrf_exempt
def track_product_click(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Not authenticated'})

    product_id = request.POST.get('product_id')
    source = request.POST.get('source', 'view')

    try:
        product = ProductsModel.objects.get(id=product_id)
        ProductClick.objects.create(
            user=request.user,
            product=product,
            source=source
        )
        return JsonResponse({'status': 'success'})
    except ProductsModel.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found'})


@require_POST
@csrf_exempt
def track_service_click(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Not authenticated'})

    service_id = request.POST.get('service_id')
    source = request.POST.get('source', 'view')

    try:
        service = ServicesModel.objects.get(id=service_id)
        ServiceClick.objects.create(
            user=request.user,
            service=service,
            source=source
        )
        return JsonResponse({'status': 'success'})
    except ServicesModel.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Service not found'})


from django.http import JsonResponse
from .models import CartItem, ServiceCartItem
from coach_dashboard.models import Coupon


@login_required
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()

        if not code:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a coupon code' if get_language() == 'en' else 'الرجاء إدخال كود الخصم'
            })

        try:
            coupon = Coupon.objects.get(code=code, is_active=True)

            # Check if coupon is valid
            student = request.user.userprofile.student_profile
            if not coupon.is_valid(student=student):
                return JsonResponse({
                    'success': False,
                    'message': 'This coupon is not valid for you' if get_language() == 'en' else 'هذا الكود غير صالح لك'
                })

            # Get cart items to check if coupon applies to them
            product_items = CartItem.objects.filter(user=request.user)
            service_items = ServiceCartItem.objects.filter(user=request.user)

            cart_items = []
            for item in product_items:
                cart_items.append({'product': item.product, 'service': None})
            for item in service_items:
                cart_items.append({'product': None, 'service': item.service})

            if not coupon.is_valid(student=student, cart_items=cart_items):
                return JsonResponse({
                    'success': False,
                    'message': 'This coupon is not valid for your cart items' if get_language() == 'en' else 'هذا الكود غير صالح للمنتجات في سلة التسوق'
                })

            # Calculate total before discount
            product_total = sum(item.total_price for item in product_items)
            service_total = sum(item.total_price for item in service_items)
            total_price = product_total + service_total

            # Calculate discount
            discount_amount = coupon.calculate_discount(total_price)
            new_total = total_price - discount_amount

            # Store coupon in session
            request.session['applied_coupon'] = {
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_value': float(coupon.discount_value),
                'max_discount': float(coupon.max_discount) if coupon.max_discount else None,
                'discount_amount': float(discount_amount),
                'coupon_id': coupon.id
            }

            return JsonResponse({
                'success': True,
                'message': 'Coupon applied successfully' if get_language() == 'en' else 'تم تطبيق الخصم بنجاح',
                'discount_amount': float(discount_amount),
                'new_total': float(new_total),
                'coupon': {
                    'code': coupon.code,
                    'discount_type': coupon.discount_type,
                    'discount_value': float(coupon.discount_value),
                    'max_discount': float(coupon.max_discount) if coupon.max_discount else None,
                    'description': coupon.description
                }
            })

        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid coupon code' if get_language() == 'en' else 'كود الخصم غير صحيح'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request' if get_language() == 'en' else 'طلب غير صالح'
    })


@login_required
def remove_coupon(request):
    if request.method == 'POST':
        if 'applied_coupon' in request.session:
            # Calculate total without discount
            product_items = CartItem.objects.filter(user=request.user)
            service_items = ServiceCartItem.objects.filter(user=request.user)

            product_total = sum(item.total_price for item in product_items)
            service_total = sum(item.total_price for item in service_items)
            total_price = product_total + service_total

            del request.session['applied_coupon']

            return JsonResponse({
                'success': True,
                'message': 'Coupon removed successfully' if get_language() == 'en' else 'تم إزالة الخصم بنجاح',
                'new_total': float(total_price)
            })

        return JsonResponse({
            'success': False,
            'message': 'No coupon applied' if get_language() == 'en' else 'لا يوجد خصم مطبق'
        })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request' if get_language() == 'en' else 'طلب غير صالح'
    })


from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# Add this new view
@login_required
def activate_coupon(request, coupon_id):
    if request.method == 'POST':
        try:
            student = request.user.userprofile.student_profile
            coupon = Coupon.objects.get(id=coupon_id, is_active=True)

            # Check if student is eligible
            if not coupon.all_students and not coupon.selected_students.filter(id=student.id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'You are not eligible for this coupon' if get_language() == 'en' else 'غير مؤهل لهذا الكوبون'
                })

            # Activate the coupon
            if coupon.activate_for_student(student):
                return JsonResponse({
                    'success': True,
                    'message': 'Coupon activated successfully' if get_language() == 'en' else 'تم تفعيل الكوبون بنجاح'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Coupon already activated' if get_language() == 'en' else 'تم تفعيل الكوبون مسبقاً'
                })

        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid coupon' if get_language() == 'en' else 'كوبون غير صالح'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request' if get_language() == 'en' else 'طلب غير صالح'
    })


from coach_dashboard.models import CouponActivation
@login_required
def student_coupon_notifications(request):
    student = request.user.userprofile.student_profile
    club = student.club

    # Get active coupons available to this student
    active_coupons = Coupon.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).filter(
        models.Q(all_students=True) |
        models.Q(selected_students=student)
    ).distinct()

    # Annotate with activation status
    coupons_with_status = []
    for coupon in active_coupons:
        try:
            activation = coupon.activations.get(student=student)
            is_activated = activation.is_active
        except CouponActivation.DoesNotExist:
            is_activated = False
        coupons_with_status.append({
            'coupon': coupon,
            'is_activated': is_activated
        })

    context = {
        'coupons_with_status': coupons_with_status,
        'club': club,
    }
    return render(request, 'student/coupons/notifications.html', context)