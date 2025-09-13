from django.shortcuts import render, redirect,get_object_or_404
from django.views.decorators.http import require_POST
import datetime, json
from students.models import ServiceOrderModel, ServicesModel,Order,OrderItem
from django.contrib.auth.models import User
from django.http import JsonResponse
from accounts.models import UserProfile,StudentProfile
from django.utils import timezone
import datetime  # ✅ Import datetime module
from .utils import send_notification
from django.contrib.auth.decorators import login_required  # ✅ Fix missing import
from django.contrib import messages
from club_dashboard.models import SalonAppointment
from datetime import datetime,timedelta
from receptionist_dashboard.models import BookingService,SalonBooking
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import translation
from django.utils.translation import get_language
from django.forms import formset_factory
from receptionist_dashboard.forms import SalonBookingForm ,ServiceSelectionForm
from django.db import models, transaction
from students.models import ProductsModel , CartItem,ServiceCartItem,OrderItem,Order

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


from coach_dashboard.models import Notification
def index(request):
    context = {}
    user = request.user
    user_profile = user.userprofile.Coach_profile

    # Verify coach access
    if not hasattr(user, 'userprofile') or not hasattr(user.userprofile, 'Coach_profile') or not user.userprofile.Coach_profile:
        messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return redirect('home')

    coach = user.userprofile.Coach_profile
    coach_id = coach.id
    lang = translation.get_language()

    notifications = Notification.objects.filter(club=user_profile).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()

    # Get statistics
    products_count = ProductsModel.objects.filter(creator=user).count()
    services_count = ServicesModel.objects.filter(creator=user).count()

    # Calculate total offers (products + services created by this coach)
    offers_count = products_count + services_count


    order_items = OrderItem.objects.filter(
        Q(order__status__in=['paid', 'delivered', 'confirmed', 'completed']),
        Q(product__creator=user) | Q(service__creator=user)
    ).distinct()

    # Calculate revenues
    credit_card_items = order_items.filter(
        order__payment_method='credit_card'
    )
    cash_items = order_items.filter(
        order__payment_method='cash_on_delivery'
    )
    pending_items = order_items.filter(
        order__status='paid'
    )

    orders = Order.objects.filter(
        Q(items__product__creator=user) | Q(items__service__creator=user)
    ).distinct()

    orders_count = orders.count()

    # Calculate vendor net profit for each category
    def calculate_vendor_net(items):
        total = Decimal('0.00')
        for item in items:
            if item.product:
                total += item.quantity * Decimal(str(item.product.vendor_net_profit))
            elif item.service:
                total += item.quantity * Decimal(str(item.service.vendor_net_profit))
        return total

    credit_card_revenue = calculate_vendor_net(credit_card_items)
    cash_revenue = calculate_vendor_net(cash_items)
    pending_revenue = calculate_vendor_net(pending_items)
    total_sales = credit_card_revenue + cash_revenue

    # Calculate monthly sales (last 6 months)
    monthly_sales = []
    for i in range(5, -1, -1):
        month = timezone.now() - timezone.timedelta(days=30 * i)
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)

        ssales = OrderItem.objects.filter(
            Q(order__created_at__range=[month_start, month_end]),
            Q(order__status__in=['paid', 'delivered', 'confirmed', 'completed']),
            Q(product__creator=user) | Q(service__creator=user)
        ).distinct()

        # Calculate revenues
        credit_card_items = ssales.filter(
            order__payment_method='credit_card'
        )
        cash_items = ssales.filter(
            order__payment_method='cash_on_delivery'
        )

        # Calculate vendor net profit for each category
        def calculate_vendor_net(items):
            total = Decimal('0.00')
            for item in items:
                if item.product:
                    total += item.quantity * Decimal(str(item.product.vendor_net_profit))
                elif item.service:
                    total += item.quantity * Decimal(str(item.service.vendor_net_profit))
            return total

        credit_card_revenue = calculate_vendor_net(credit_card_items)
        cash_revenue = calculate_vendor_net(cash_items)
        sales = credit_card_revenue + cash_revenue

        monthly_sales.append({
            'month': month_start.strftime('%b %Y'),
            'sales': sales
        })

    # Student analysis
    students = User.objects.filter(
        Q(orders__items__product__creator=user) | Q(orders__items__service__creator=user)
    ).annotate(
        order_count=Count('orders', filter=Q(
            Q(orders__items__product__creator=user) | Q(orders__items__service__creator=user)
        ))
    ).distinct()

    new_students = students.filter(
        orders__created_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).distinct().count()

    returning_students = students.count() - new_students

    # Get latest 3 reviews
    latest_reviews = Review.objects.filter(
        Q(product__creator=user) | Q(service__creator=user)
    ).order_by('-created_at')[:3]

    # Get appointments (existing code)
    try:
        confirmed_appointments = []
        # ... (keep your existing appointment query code)

        last_four_appointments = confirmed_appointments[:4]
    except Exception as e:
        print(f"Error retrieving appointments: {str(e)}")
        last_four_appointments = []

    club = coach.club if coach and hasattr(coach, 'club') else None

    context.update({
        'LANGUAGE_CODE': lang,
        'CoachAppointments': last_four_appointments,
        'coachName': coach.full_name,
        'coachId': coach_id,
        'products_count': products_count,
        'services_count': services_count,
        'offers_count': offers_count,
        'students_count': students.count(),
        'latest_reviews': latest_reviews,
        'notifications': notifications,
        'unread_count': unread_count,
        'total_sales': total_sales,
        'orders_count':orders_count,
        'monthly_sales': monthly_sales,
        'new_students': new_students,
        'returning_students': returning_students,
    })

    return render(request, 'coach_dashboard/index.html', context)


@login_required
def mark_notifications_read(request):
    user = request.user
    user_profile = user.userprofile.Coach_profile
    if request.method == 'POST':
        # Mark all unread notifications for this user as read
        Notification.objects.filter(
            club=user_profile,
            is_read=False
        ).update(is_read=True)

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
def view_coach_profile(request):
    """View the coach's own profile"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        coach = user_profile.Coach_profile

        if not coach:
            messages.error(request, "لا يوجد ملف شخصي للمدرب")
            return redirect('dashboard')  # Redirect to a suitable page

        # Get additional context data
        context = {
            'coach': coach,
            'userprofile': user_profile,
            'activity_types': CoachProfile.activity_type,
            'approval_statuses': dict(CoachProfile.APPROVAL_STATUS_CHOICES),
            'business_document_types': dict(CoachProfile.BUSINESS_DOCUMENT_CHOICES),
        }
        context['LANGUAGE_CODE'] = translation.get_language()
        return render(request, 'accounts/profiles/Coach/ViewCoachProfile.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, "لا يوجد ملف شخصي")
        return redirect('dashboard')  # Redirect to a suitable page

from .forms import CoachProfileForm
@login_required
def edit_coach_profile(request):
    """Edit the coach's profile"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        coach = user_profile.Coach_profile

        if not coach:
            messages.error(request, "لا يوجد ملف شخصي للمدرب")
            return redirect('dashboard')

        if request.method == 'POST':
            form = CoachProfileForm(request.POST, request.FILES, instance=coach)
            if form.is_valid():
                # Save the form data
                coach_profile = form.save(commit=False)

                # Handle profile image upload
                if 'profile_image_base64' in request.FILES:
                    image_file = request.FILES['profile_image_base64']
                    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

                    # Save to both coach profile and user profile
                    coach_profile.profile_image_base64 = f"data:image/{image_file.content_type.split('/')[-1]};base64,{encoded_image}"
                    user_profile.profile_image_base64 = coach_profile.profile_image_base64
                    user_profile.save()

                # Handle business document upload
                if 'business_document_file' in request.FILES:
                    doc_file = request.FILES['business_document_file']
                    encoded_doc = base64.b64encode(doc_file.read()).decode('utf-8')
                    file_type = doc_file.content_type
                    coach_profile.business_document_file = f"data:{file_type};base64,{encoded_doc}"

                coach_profile.save()
                messages.success(request, "تم تحديث الملف الشخصي بنجاح")
                return redirect('view_coach_profile')
            else:
                messages.error(request, "يرجى تصحيح الأخطاء في النموذج")
        else:
            form = CoachProfileForm(instance=coach)

        context = {
            'form': form,
            'coach': coach,
            'activity_choices': CoachProfile.activity_type,
            'business_document_choices': CoachProfile.BUSINESS_DOCUMENT_CHOICES,
        }
        context['LANGUAGE_CODE'] = translation.get_language()
        return render(request, 'accounts/settings/Coach/EditCoachProfile.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, "لا يوجد ملف شخصي")
        return redirect('dashboard')

import logging
from django.db import connection
logger = logging.getLogger(__name__)


from club_dashboard.forms import ProductsModelForm
from students.models import ProductsModel
from club_dashboard.models import ProductImg
from django.core.paginator import Paginator
def addProduct(request):
    print("=== DEBUG: addProduct function started ===")
    context = {}
    user = request.user
    print(f"DEBUG: User: {user}")
    print(f"DEBUG: User is authenticated: {user.is_authenticated}")

    coach_profile = getattr(user.userprofile, 'Coach_profile', None)
    if not coach_profile:
        messages.error(request, "لا تملك صلاحية الوصول كمدرب.")
        return redirect('some_error_page')

    club = coach_profile.club

    if not request.user.userprofile.Coach_profile.policies_approved:
        messages.error(request, "يجب عليك رفع سياسة الشروط والأحكام وسياسة الاسترجاع أولاً")
        return redirect('upload_policies')

    print(f"DEBUG: Request method: {request.method}")


    # Initialize form with coach_profile
    form = ProductsModelForm(coach_profile=coach_profile)
    print("DEBUG: Form initialized")

    if request.method == 'POST':
        print("DEBUG: Processing POST request")
        print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
        print(f"DEBUG: POST data: {dict(request.POST)}")

        form = ProductsModelForm(data=request.POST, coach_profile=coach_profile)
        print("DEBUG: Form created with POST data")

        if form.is_valid():
            print("DEBUG: Form is valid")
            print(f"DEBUG: Form cleaned data: {form.cleaned_data}")

            try:
                product = form.save(commit=False)
                print(f"DEBUG: Product created (not saved): {product}")

                # Set product attributes
                product.club = club
                product.creator = user
                product.creation_date = timezone.now()
                print(f"DEBUG: Product club set to: {product.club}")
                print(f"DEBUG: Product creator set to: {product.creator}")
                print(f"DEBUG: Product creation_date set to: {product.creation_date}")

                # Set initial approval status
                product.approval_status = 'pending'
                product.is_enabled = False
                print(f"DEBUG: Product approval_status: {product.approval_status}")
                print(f"DEBUG: Product is_enabled: {product.is_enabled}")

                # Save the product to get an ID
                product.save()
                print(f"DEBUG: Product saved successfully with ID: {product.id}")

                # Save many-to-many relationships if any
                form.save_m2m()
                print("DEBUG: Many-to-many relationships saved")

                # Handle product images
                profile_imgs = request.POST.getlist('profile_imgs')
                print(f"DEBUG: Number of profile images: {len(profile_imgs)}")

                for i, img_data in enumerate(profile_imgs):
                    print(f"DEBUG: Processing image {i+1}")
                    print(f"DEBUG: Image data length: {len(img_data) if img_data else 0}")

                    if ';base64,' in img_data:
                        print(f"DEBUG: Image {i+1} contains base64 data")

                        try:
                            format, imgstr = img_data.split(';base64,')
                            ext = format.split('/')[-1] if '/' in format else 'png'
                            print(f"DEBUG: Image {i+1} format: {format}, extension: {ext}")

                            from django.core.files.base import ContentFile
                            import base64, uuid

                            # Generate unique filename
                            filename = f'{uuid.uuid4()}.{ext}'
                            print(f"DEBUG: Generated filename: {filename}")

                            # Decode base64 data
                            decoded_data = base64.b64decode(imgstr)
                            print(f"DEBUG: Decoded data size: {len(decoded_data)} bytes")

                            data = ContentFile(decoded_data, name=filename)
                            print(f"DEBUG: ContentFile created for image {i+1}")

                            # Create ProductImg object
                            product_img = ProductImg.objects.create(
                                product=product,
                                img=data
                            )
                            print(f"DEBUG: ProductImg created with ID: {product_img.id}")

                        except Exception as img_error:
                            print(f"DEBUG ERROR: Failed to process image {i+1} - {img_error}")
                            import traceback
                            print(f"DEBUG ERROR TRACEBACK: {traceback.format_exc()}")
                    else:
                        print(f"DEBUG: Image {i+1} does not contain base64 data")

                print("DEBUG: All images processed successfully")
                messages.success(request, 'تم إرسال المنتج للمراجعة! سيتم إعلامك عند الموافقة عليه.')
                print("DEBUG: Success message added")

                print("DEBUG: Redirecting to coachviewProducts")
                return redirect('coachviewProducts')

            except Exception as save_error:
                print(f"DEBUG ERROR: Failed to save product - {save_error}")
                import traceback
                print(f"DEBUG ERROR TRACEBACK: {traceback.format_exc()}")

        else:
            print("DEBUG: Form is NOT valid")
            print(f"DEBUG: Form errors: {form.errors}")
            print(f"DEBUG: Form non-field errors: {form.non_field_errors()}")

    commission_rate = 5  # Default rate
    if (hasattr(request.user, 'userprofile') and
            hasattr(request.user.userprofile, 'Coach_profile')):
        commission_rate = request.user.userprofile.Coach_profile.get_current_commission_rate()

    print("DEBUG: Preparing context and rendering template")
    context['LANGUAGE_CODE'] = translation.get_language()
    print(f"DEBUG: Language code: {context['LANGUAGE_CODE']}")
    print(f"DEBUG: Final context keys: {list(context.keys())}")

    print("DEBUG: Rendering template")
    return render(request, 'coach_dashboard/products/ProductsStock/addProductStock.html', {
        'form': form,
        'club': club,
        'commission_rate': commission_rate,
        'coach_profile': coach_profile
    })

def editProduct(request, id):
    context = {}
    user = request.user
    product = ProductsModel.objects.get(id=id)
    profile_img_objs = ProductImg.objects.filter(product=product)
    form = ProductsModelForm(instance=product)
    club = getattr(user.userprofile.Coach_profile, 'club', None)

    if request.method == 'POST':
        form = ProductsModelForm(data=request.POST, instance=product)
        if form.is_valid():
            profile_imgs = request.POST.getlist('profile_imgs')
            images_changed = request.POST.get('images_changed', 'false') == 'true'

            updated_product = form.save(commit=False)
            updated_product.updated_at = timezone.now()
            updated_product.save()
            form.save_m2m()

            if images_changed:
                ProductImg.objects.filter(product=product).delete()

                for img_data in profile_imgs:
                    if img_data.startswith('data:image'):
                        format, imgstr = img_data.split(';base64,')
                        ext = format.split('/')[-1]

                        import uuid
                        filename = f"{uuid.uuid4()}.{ext}"

                        from django.core.files.base import ContentFile
                        import base64
                        data = ContentFile(base64.b64decode(imgstr))

                        img_obj = ProductImg(product=product)
                        img_obj.img.save(filename, data, save=False)
                        img_obj.save()

            messages.success(request, 'تم تعديل المنتج بنجاح')
            return redirect('coachviewProducts')

    commission_rate = 5  # Default rate
    if (hasattr(request.user, 'userprofile') and
            hasattr(request.user.userprofile, 'Coach_profile')):
        commission_rate = request.user.userprofile.Coach_profile.get_current_commission_rate()

    context = {
        'form': form,
        'profile_imgs': profile_img_objs,
        'club' :club,
        'product': product,
        'commission_rate': commission_rate,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/products/ProductsStock/editProductStock.html', context)

def viewProducts(request):
    context = {}
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None)
    products = ProductsModel.objects.filter(creator=user)
    total_products = products.count()

    total_value = 0
    low_stock_count = 0
    out_of_stock_count = 0
    expiring_soon_count = 0
    expired_count = 0
    low_stock_threshold = 10

    for product in products:
        product_value = product.price * product.stock
        total_value += product_value

        if 0 < product.stock <= low_stock_threshold:
            low_stock_count += 1

        if product.stock == 0:
            out_of_stock_count += 1

        if product.is_expiring_soon:
            expiring_soon_count += 1

        if product.is_expired:
            expired_count += 1

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page', 1)
    paginated_products = paginator.get_page(page_number)

    context = {
        'products': paginated_products,
        'total_products': total_products,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'expiring_soon_count': expiring_soon_count,
        'expired_count': expired_count,
        'low_stock_threshold': low_stock_threshold,
        'club':club
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/products/ProductsStock/viewProductsStock.html', context)


def DeleteProduct(request, id):
    art = get_object_or_404(ProductsModel, id=id)
    art.delete()
    messages.success(request, 'تم حذف المنتج بنجاح!')
    return redirect('coachviewProducts')

from club_dashboard.forms import ProductShipmentForm
def edit_shipment(request, shipment_id):
    """Edit a product shipment"""
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None)

    try:
        shipment = ProductShipment.objects.get(id=shipment_id, product__club=club)
    except ProductShipment.DoesNotExist:
        messages.error(request, 'الشحنة غير موجودة!' if translation.get_language() == 'ar' else 'Shipment not found!')
        return redirect('coachviewProducts')

    if request.method == 'POST':
        form = ProductShipmentForm(request.POST, instance=shipment, club=club)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الشحنة بنجاح!' if translation.get_language() == 'ar' else 'Shipment updated successfully!')
            return redirect('coachview_product_shipments', product_id=shipment.product.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه.' if translation.get_language() == 'ar' else 'Please correct the errors below.')
    else:
        form = ProductShipmentForm(instance=shipment, club=club)

    context = {
        'form': form,
        'shipment': shipment,
        'product': shipment.product,
        'club': club,
        'LANGUAGE_CODE': translation.get_language(),
        'is_edit': True,
    }

    return render(request, 'coach_dashboard/products/ProductsStock/add_edit_shipment.html', context)


def delete_shipment(request, shipment_id):
    """Delete a product shipment"""
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None)

    try:
        shipment = ProductShipment.objects.get(id=shipment_id, product__club=club)
        product_id = shipment.product.id
        product_title = shipment.product.title
        quantity = shipment.quantity

        shipment.delete()

        messages.success(
            request,
            f'تم حذف شحنة المنتج "{product_title}" بكمية {quantity} وحدة بنجاح!'
            if translation.get_language() == 'ar'
            else f'Shipment for product "{product_title}" with quantity {quantity} units deleted successfully!'
        )

        return redirect('coachview_product_shipments', product_id=product_id)

    except ProductShipment.DoesNotExist:
        messages.error(request, 'الشحنة غير موجودة!' if translation.get_language() == 'ar' else 'Shipment not found!')
        return redirect('coachviewProducts')


# Update your existing add_shipment view to use the same template
def add_shipment(request):
    """Add a new product shipment"""
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None)

    # Get product_id from URL parameters if provided
    product_id = request.GET.get('product_id')
    product = None

    if product_id:
        try:
            product = ProductsModel.objects.get(id=product_id, club=club)
        except ProductsModel.DoesNotExist:
            messages.error(request, 'المنتج غير موجود!' if translation.get_language() == 'ar' else 'Product not found!')
            return redirect('coachviewProducts')

    if request.method == 'POST':
        form = ProductShipmentForm(request.POST, club=club)
        if form.is_valid():
            shipment = form.save()
            messages.success(request, 'تمت إضافة الشحنة بنجاح!' if translation.get_language() == 'ar' else 'Shipment added successfully!')
            return redirect('coachview_product_shipments', product_id=shipment.product.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه.' if translation.get_language() == 'ar' else 'Please correct the errors below.')
    else:
        form = ProductShipmentForm(club=club)
        # Pre-select the product if provided
        if product:
            form.fields['product'].initial = product

    context = {
        'form': form,
        'product': product,
        'club': club,
        'LANGUAGE_CODE': translation.get_language(),
        'is_edit': False,
    }

    return render(request, 'coach_dashboard/products/ProductsStock/add_edit_shipment.html', context)

def view_product_shipments(request, product_id):
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None)


    try:
        product = ProductsModel.objects.get(id=product_id, club=club)
    except ProductsModel.DoesNotExist:
        messages.error(request, 'المنتج غير موجود!')
        return redirect('coachviewProducts')

    shipments = ProductShipment.objects.filter(product=product).order_by('-created_at')

    expiring_soon_count = sum(1 for s in shipments if s.is_expiring_soon)
    expired_count = sum(1 for s in shipments if s.is_expired)
    valid_count = len(shipments) - expiring_soon_count - expired_count

    total_quantity = sum(s.quantity for s in shipments)
    expiring_soon_quantity = sum(s.quantity for s in shipments if s.is_expiring_soon)
    expired_quantity = sum(s.quantity for s in shipments if s.is_expired)
    valid_quantity = total_quantity - expiring_soon_quantity - expired_quantity

    context = {
        'product': product,
        'shipments': shipments,
        'stats': {
            'total_count': len(shipments),
            'expiring_soon_count': expiring_soon_count,
            'expired_count': expired_count,
            'valid_count': valid_count,
            'total_quantity': total_quantity,
            'expiring_soon_quantity': expiring_soon_quantity,
            'expired_quantity': expired_quantity,
            'valid_quantity': valid_quantity,
        },
        'club':club,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/products/ProductsStock/view_product_shipments.html', context)


from club_dashboard.models import ProductShipment
def product_details(request, product_id):
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None)

    try:
        product = ProductsModel.objects.get(id=product_id, club=club)
    except ProductsModel.DoesNotExist:
        messages.error(request, 'المنتج غير موجود!')
        return redirect('coachviewProducts')

    product_images = product.product_images.all()

    shipments = ProductShipment.objects.filter(product=product).order_by('-created_at')

    expiring_soon_count = sum(1 for s in shipments if s.is_expiring_soon)
    expired_count = sum(1 for s in shipments if s.is_expired)
    valid_count = len(shipments) - expiring_soon_count - expired_count

    total_quantity = sum(s.quantity for s in shipments)
    expiring_soon_quantity = sum(s.quantity for s in shipments if s.is_expiring_soon)
    expired_quantity = sum(s.quantity for s in shipments if s.is_expired)
    valid_quantity = total_quantity - expiring_soon_quantity - expired_quantity

    context = {
        'product': product,
        'product_images': product_images,
        'shipments': shipments,
        'stats': {
            'total_count': len(shipments),
            'expiring_soon_count': expiring_soon_count,
            'expired_count': expired_count,
            'valid_count': valid_count,
            'total_quantity': total_quantity,
            'expiring_soon_quantity': expiring_soon_quantity,
            'expired_quantity': expired_quantity,
            'valid_quantity': valid_quantity,
        },
        'club':club,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/products/ProductsStock/product_details.html', context)



from accounts.models import CoachProfile
from club_dashboard.forms import ServicesModelForm, ServicesClassificationModelForm
from students.models import ServicesClassificationModel
from decimal import Decimal
import time
from django.core.files.base import ContentFile
import base64
def addServices(request):
    context = {}
    user = request.user
    coach_profile = getattr(user.userprofile, 'Coach_profile', None)
    club = getattr(coach_profile, 'club', None) if coach_profile else None

    if not coach_profile:
        messages.error(request, "لا تملك صلاحية الوصول كمدرب.")
        return redirect('some_error_page')

    coaches = CoachProfile.objects.filter(club=club)
    classifications = ServicesClassificationModel.objects.filter(club=club)

    if not request.user.userprofile.Coach_profile.policies_approved:
        messages.error(request, "يجب عليك رفع سياسة الشروط والأحكام وسياسة الاسترجاع أولاً")
        return redirect('upload_policies')

    # Initialize form with coach_profile
    form = ServicesModelForm(coach_profile=coach_profile)
    form.fields['coaches'].queryset = coaches
    form.fields['classification'].queryset = classifications

    if request.method == 'POST':
        form = ServicesModelForm(data=request.POST, coach_profile=coach_profile)
        form.fields['coaches'].queryset = coaches
        form.fields['classification'].queryset = classifications

        if form.is_valid():
            ser = form.save(commit=False)
            ser.club = club
            ser.creator = user
            ser.creation_date = timezone.now()

            ser.age_from = 0
            ser.age_to = 100
            ser.subscription_days = 30

            duration = request.POST.get('duration')
            if duration:
                ser.duration = int(duration)
            else:
                ser.duration = 0

            discounted_price = request.POST.get('discounted_price')
            if discounted_price and discounted_price.strip():
                ser.discounted_price = Decimal(discounted_price)

            # Set initial approval status
            ser.approval_status = 'pending'
            ser.is_enabled = False

            ser.save()

            # Handle coaches (many-to-many)
            form.save_m2m()

            # Handle classification (single selection for many-to-many field)
            selected_classification = form.cleaned_data.get('classification')
            if selected_classification:
                ser.classification.set([selected_classification])

            image_data = request.POST.get('service_image_data')
            if image_data and image_data.startswith('data:image'):
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]

                filename = f"service_{ser.id}_{int(time.time())}.{ext}"
                temp_file = ContentFile(base64.b64decode(imgstr), name=filename)

                ser.image.save(filename, temp_file, save=True)

            messages.success(request, 'تم إرسال الخدمة للمراجعة! سيتم إعلامك عند الموافقة عليها.')
            return redirect('coachviewServices')
        else:
            print(form.errors)

    commission_rate = 5  # Default rate
    if (hasattr(request.user, 'userprofile') and
            hasattr(request.user.userprofile, 'Coach_profile')):
        commission_rate = request.user.userprofile.Coach_profile.get_current_commission_rate()

    context['LANGUAGE_CODE'] = translation.get_language()
    selected_coach_ids = request.POST.getlist('coaches') if request.method == 'POST' else []
    selected_classification_id = request.POST.get('classification') if request.method == 'POST' else None

    return render(request, 'coach_dashboard/services/addServices.html', {
        'form': form,
        'selected_coach_ids': selected_coach_ids,
        'selected_classification_id': selected_classification_id,
        'club': club,
        'commission_rate': commission_rate,
        'coach_profile': coach_profile
    })


from decimal import Decimal
def editServices(request, id):
    context = {}
    ser = ServicesModel.objects.get(id=id)
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None)
    classifications = ServicesClassificationModel.objects.filter(club=club)

    coaches = CoachProfile.objects.filter(club=club)
    form = ServicesModelForm(instance=ser)
    form.fields['coaches'].queryset = coaches
    form.fields['classification'].queryset = classifications

    if request.method == 'POST':
        form = ServicesModelForm(data=request.POST, instance=ser)
        form.fields['coaches'].queryset = coaches
        form.fields['classification'].queryset = classifications
        if form.is_valid():
            ser = form.save(commit=False)
            ser.creation_date = timezone.now()

            duration = request.POST.get('duration')
            ser.duration = int(duration) if duration else 0

            discounted_price = request.POST.get('discounted_price')
            if discounted_price and discounted_price.strip():
                ser.discounted_price = Decimal(discounted_price)
            else:
                ser.discounted_price = None

            # Check if the current image should be removed
            remove_current_image = request.POST.get('remove_current_image')
            if remove_current_image == 'true' and ser.image:
                # Delete the old image file
                ser.image.delete(save=False)

            # Handle classification (single selection for many-to-many field)
            selected_classification = form.cleaned_data.get('classification')
            if selected_classification:
                ser.classification.set([selected_classification])

            # Process new image upload if available
            image_data = request.POST.get('service_image_data')
            if image_data and image_data.startswith('data:image'):
                # Get the format and the actual base64 data
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]

                # Generate filename and save path
                filename = f"service_{ser.id}_{int(time.time())}.{ext}"
                temp_file = ContentFile(base64.b64decode(imgstr), name=filename)

                # If there's an existing image, delete it first
                if ser.image:
                    ser.image.delete(save=False)

                # Save to the model's ImageField
                ser.image.save(filename, temp_file, save=False)

            ser.save()
            form.save_m2m()
            return redirect('coachviewServices')
        else:
            print(form.errors)

    context['LANGUAGE_CODE'] = translation.get_language()
    context['current_user'] = request.user

    # Get the current coaches and classification for the service
    current_coaches = ser.coaches.all()
    selected_coach_ids = [str(coach.id) for coach in current_coaches]

    # Get the current classification (assuming single selection)
    current_classification = ser.classification.first()
    selected_classification_id = str(current_classification.id) if current_classification else None

    commission_rate = 5  # Default rate
    if (hasattr(request.user, 'userprofile') and
            hasattr(request.user.userprofile, 'Coach_profile')):
        commission_rate = request.user.userprofile.Coach_profile.get_current_commission_rate()

    # Add pricing period choices to context
    context.update({
        'form': form,
        'selected_coach_ids': selected_coach_ids,
        'club': club,
        'selected_classification_id': selected_classification_id,
        'commission_rate': commission_rate,
        'pricing_period_choices': ServicesModel.PRICING_PERIOD_CHOICES,
    })

    return render(request, 'coach_dashboard/services/editServices.html', context)


def viewServices(request):
    context = {}
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None)
    services = ServicesModel.objects.filter(creator=user)

    if services:
        # Calculate average monthly price (normalize all prices to monthly rate)
        total_monthly_price = sum(service.monthly_price for service in services)
        avg_monthly_price = total_monthly_price / len(services)
        avg_monthly_price = round(avg_monthly_price, 1)

        # Calculate average duration
        avg_duration = sum(service.duration for service in services) / len(services)
        avg_duration_hours = int(avg_duration // 60)
        avg_duration_minutes = int(avg_duration % 60)

        # Calculate pricing period statistics
        pricing_periods = [service.pricing_period_months for service in services]
        most_common_period = max(set(pricing_periods), key=pricing_periods.count)

        # Get pricing period choices for display
        pricing_period_choices = dict(ServicesModel.PRICING_PERIOD_CHOICES)

    else:
        avg_monthly_price = 0
        avg_duration_hours = 0
        avg_duration_minutes = 0
        most_common_period = 1
        pricing_period_choices = dict(ServicesModel.PRICING_PERIOD_CHOICES)

    context = {
        'services': services,
        'avg_monthly_price': avg_monthly_price,
        'avg_duration_hours': avg_duration_hours,
        'avg_duration_minutes': avg_duration_minutes,
        'most_common_period': most_common_period,
        'pricing_period_choices': pricing_period_choices,
        'club': club,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/services/viewServices.html', context)

def viewServiceDetails(request, service_id):
    context = {}
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None)

    try:
        service = ServicesModel.objects.get(id=service_id, club=club)
    except ServicesModel.DoesNotExist:
        messages.error(request, 'Service not found.')
        return redirect('coachviewServices')

    context = {
        'service': service,
        'club': club,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/services/viewServiceDetails.html', context)

def DeleteServices(request, id):
    art = ServicesModel.objects.get(id=id)
    art.delete()
    return redirect('coachviewServices')

def addServicesClassification(request):
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None)
    form = ServicesClassificationModelForm()
    if request.method == 'POST':
        form = ServicesClassificationModelForm(data=request.POST)
        if form.is_valid():
            cla = form.save(commit=False)
            cla.club = club
            cla.creator = user
            cla.creation_date = timezone.now()
            cla.save()


    return render(request, 'coach_dashboard/services/Classification/addClassification.html', {'form':form})

def editServicesClassification(request, id):
    cla = ServicesClassificationModel.objects.get(id=id)
    form = ServicesClassificationModelForm(instance=cla)
    if request.method == 'POST':
        form = ServicesClassificationModelForm(data=request.POST, instance=cla)
        if form.is_valid():
            form.save()

    return render(request, 'coach_dashboard/services/Classification/editClassification.html', {'form':form})

def viewServicesClassification(request):
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None)
    classifications = ServicesClassificationModel.objects.filter(club=club)
    return render(request, 'coach_dashboard/services/Classification/viewClassification.html', {'classifications':classifications})

def DeleteServicesClassification(request, id):
    art = ServicesClassificationModel.objects.get(id=id)
    art.delete()
    return redirect('coachviewServicesClassification')

from .models import Notification


@login_required
def viewCoachNotifications(request):
    context = {}
    """Displays all coach notifications and marks them as read."""
    user = request.user

    club = getattr(user.userprofile.Coach_profile, 'club', None)
    coach = getattr(user.userprofile, 'Coach_profile', None)

    notifications = Notification.objects.filter(club=coach).order_by('-created_at')

    # Mark all unread notifications as read
    unread_count = notifications.filter(is_read=False).update(is_read=True)

    # Filter by notification type if requested
    notification_type = request.GET.get('type')
    if notification_type and notification_type in dict(Notification.NOTIFICATION_TYPES).keys():
        notifications = notifications.filter(notification_type=notification_type)

    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/notifications/viewCoachNotifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
        'club': club,
        'notification_types': Notification.NOTIFICATION_TYPES,
        'current_type': notification_type,
    })


def delete_notification(request, notification_id):
    """Delete a specific notification"""
    user = request.user
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id)
            # Check if the notification belongs to the user's club
            club = getattr(user.userprofile.Coach_profile, 'club', None)
            if notification.club == club:
                notification.delete()
                messages.success(request, "Notification deleted successfully.")
            else:
                messages.error(request, "You don't have permission to delete this notification.")
        except Notification.DoesNotExist:
            messages.error(request, "Notification not found.")

    return redirect('viewCoachNotifications')

def delete_all_notifications(request):
    user = request.user
    """Delete all notifications for the club"""
    if request.method == 'POST':
        club = getattr(user.userprofile.Coach_profile, 'club', None)
        if club:
            deleted_count, _ = Notification.objects.filter(club=club).delete()
            messages.success(request, f"Deleted {deleted_count} notifications.")
        else:
            messages.error(request, "No club associated with your account.")

    return redirect('viewCoachNotifications')



def viewOrders(request):
    context = {}
    user = request.user
    coach_profile = user.userprofile.Coach_profile
    club = getattr(coach_profile, 'club', None)

    # Get orders that contain products or services created by this coach
    orders = Order.objects.filter(
        Q(items__product__creator=user) | Q(items__service__coaches=coach_profile),
        club=club
    ).distinct().order_by('-created_at')

    # Calculate status counts
    total_orders = orders.count()
    paid_orders = orders.filter(status='paid').count()
    delivered_orders = orders.filter(status='delivered').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    completed_orders = orders.filter(status='completed').count()
    pending_orders = orders.filter(status='pending').count()

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter and status_filter in dict(Order.STATUS_CHOICES).keys():
        orders = orders.filter(status=status_filter)

    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'total_orders': total_orders,
        'paid_orders': paid_orders,
        'delivered_orders': delivered_orders,
        'confirmed_orders': confirmed_orders,
        'cancelled_orders': cancelled_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'status_filter': status_filter,
        'club': club,
    }

    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/orders/viewCoachOrders.html', context)


@login_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        user = request.user
        coach_profile = user.userprofile.Coach_profile

        try:
            order = Order.objects.get(
                id=order_id,
                items__product__creator=user  # Only allow coach to update their own orders
            )

            new_status = request.POST.get('status')

            # Validate status transition
            valid_transitions = {
                'pending': ['paid', 'cancelled'],
                'paid': ['delivered', 'cancelled'],
                'delivered': ['confirmed', 'cancelled'],
            }

            if new_status not in valid_transitions.get(order.status, []):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid status transition'
                }, status=400)

            # Update order status
            order.status = new_status
            order.save()

            # Create notification if needed
            if new_status == 'delivered':
                Notification.objects.create(
                    club=coach_profile.club,
                    message=f'طلب جديد يحتاج إلى تأكيد #{order.id}',
                    is_read=False,
                    created_at=timezone.now()
                )

            return JsonResponse({
                'status': 'success',
                'message': f'تم تحديث حالة الطلب إلى {dict(Order.STATUS_CHOICES)[new_status]}'
            })

        except Order.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Order not found or unauthorized'
            }, status=404)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)


from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import HttpResponse
import tempfile
def viewOrderDetails(request, order_id):
    context = {}
    user = request.user
    coach_profile = user.userprofile.Coach_profile
    club = getattr(coach_profile, 'club', None)

    try:
        order = Order.objects.get(
            Q(items__product__creator=user) | Q(items__service__coaches=coach_profile),
            id=order_id,
            club=club
        )
    except Order.DoesNotExist:
        messages.error(request, "Order not found or you don't have permission to view it.")
        return redirect('coachviewOrders')

    # Filter items to show only those belonging to this coach
    coach_items = order.items.filter(
        Q(product__creator=user) | Q(service__coaches=coach_profile))

    # Calculate total price for coach's items only
    coach_total = sum(item.get_total() for item in coach_items)

    context = {
        'order': order,
        'coach_items': coach_items,
        'coach_total': coach_total,
        'club': club,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/orders/coachOrderDetails.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.utils import translation, timezone
from django.template.loader import render_to_string
import qrcode
import io
import base64
from decimal import Decimal
from students.models import Order


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import BusinessProfileForm  # We'll create this form next
from accounts.models import CoachProfile

@login_required
def view_business_profile(request):
    """View the coach's business profile"""
    try:
        user_profile = request.user.userprofile
        coach = user_profile.Coach_profile

        if not coach:
            messages.error(request, "No coach profile found")
            return redirect('dashboard')

        context = {
            'coach': coach,
            'user_profile' : user_profile,
            'activity_types': CoachProfile.activity_type,
            'business_document_types': dict(CoachProfile.BUSINESS_DOCUMENT_CHOICES),
            'LANGUAGE_CODE': translation.get_language(),
        }
        return render(request, 'coach_dashboard/business_profile/view_business_profile.html', context)

    except UserProfile.DoesNotExist:
        messages.error(request, "No user profile found")
        return redirect('dashboard')


import re
@login_required
def edit_bank_info(request):
    """Edit the coach's bank information"""
    try:
        user_profile = request.user.userprofile
        coach = user_profile.Coach_profile

        if request.method == 'POST':
            bank_name = request.POST.get('bank_name', '')
            account_name = request.POST.get('account_name', '')
            account_number = request.POST.get('account_number', '')
            iban = request.POST.get('iban', '')

            # Clean and validate IBAN
            cleaned_iban = iban.replace(' ', '').upper()  # Remove spaces and convert to uppercase
            iban_pattern = re.compile(r'^[A-Z0-9]{4}8060[A-Z0-9]{4}800012SA1212$')

            if not iban_pattern.match(cleaned_iban):
                messages.error(request, "Invalid IBAN format. Please use format: XXXX 8060 XXXX 8000 12SA 1212")
                context = {
                    'coach': coach,
                    'LANGUAGE_CODE': translation.get_language(),
                }
                return render(request, 'coach_dashboard/business_profile/edit_bank_info.html', context)

            # If validation passes, save the data
            coach.bank_name = bank_name
            coach.account_name = account_name
            coach.account_number = account_number
            coach.iban = cleaned_iban  # Store without spaces
            coach.save()

            messages.success(request, "Bank information updated successfully")
            return redirect('view_business_profile')

        context = {
            'coach': coach,
            'LANGUAGE_CODE': translation.get_language(),
        }
        return render(request, 'coach_dashboard/business_profile/edit_bank_info.html', context)

    except UserProfile.DoesNotExist:
        messages.error(request, "No user profile found")
        return redirect('dashboard')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import translation
from django.conf import settings
import base64
import json
from .models import CoachProfile, UserProfile
from .forms import BusinessProfileForm
from club_dashboard.models import Category
@login_required
def edit_business_profile(request):
    """Edit the coach's business profile"""
    try:
        user_profile = request.user.userprofile
        coach = user_profile.Coach_profile
        if not coach:
            messages.error(request, "No coach profile found")
            return redirect('dashboard')

        if request.method == 'POST':
            form = BusinessProfileForm(request.POST, request.FILES, instance=coach)
            if form.is_valid():
                # Handle business document upload
                if 'business_document_file' in request.FILES:
                    doc_file = request.FILES['business_document_file']
                    encoded_doc = base64.b64encode(doc_file.read()).decode('utf-8')
                    file_type = doc_file.content_type
                    form.instance.business_document_file = f"data:{file_type};base64,{encoded_doc}"

                # Handle business photo upload
                if 'business_photo' in request.FILES:
                    photo_file = request.FILES['business_photo']
                    encoded_photo = base64.b64encode(photo_file.read()).decode('utf-8')
                    file_type = photo_file.content_type
                    form.instance.business_photo_base64 = f"data:{file_type};base64,{encoded_photo}"

                # Handle phone numbers from POST data
                phone_numbers = request.POST.getlist('business_phone_numbers')
                form.instance.business_phone_numbers = [num.strip() for num in phone_numbers if num.strip()]

                form.save()
                messages.success(request, "Business profile updated successfully")
                return redirect('view_business_profile')
            else:
                # Print form errors for debugging
                print("Form errors:", form.errors)
        else:
            form = BusinessProfileForm(instance=coach)

        # Get activity types from Category model
        activity_types = Category.objects.all()

        context = {
            'form': form,
            'coach': coach,
            'activity_choices': activity_types,
            'business_document_choices': CoachProfile.BUSINESS_DOCUMENT_CHOICES,
            'LANGUAGE_CODE': translation.get_language(),
        }
        return render(request, 'coach_dashboard/business_profile/edit_business_profile.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, "No user profile found")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('dashboard')


from students.models import Review


@login_required
def coach_reviews(request):
    context = {}
    user = request.user

    # Verify coach access
    if not hasattr(user, 'userprofile') or not hasattr(user.userprofile, 'Coach_profile'):
        messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return redirect('home')

    coach = user.userprofile.Coach_profile
    lang = translation.get_language()

    try:
        # Get products and services created by this coach
        products = ProductsModel.objects.filter(creator=user)
        services = ServicesModel.objects.filter(creator=user)

        # Get reviews for these products and services
        product_reviews = Review.objects.filter(product__in=products).select_related(
            'student', 'product', 'order', 'order_item'
        )
        service_reviews = Review.objects.filter(service__in=services).select_related(
            'student', 'service', 'order', 'order_item'
        )

        # Combine and sort by date
        all_reviews = list(product_reviews) + list(service_reviews)
        all_reviews.sort(key=lambda x: x.created_at, reverse=True)

        # Counts for stats cards based on order status
        total_reviews = len(all_reviews)
        confirmed_reviews = len([r for r in all_reviews if r.order.status == 'confirmed'])
        completed_reviews = len([r for r in all_reviews if r.order.status == 'completed'])
        pending_reviews = len([r for r in all_reviews if r.order.status == 'pending'])
        cancelled_reviews = len([r for r in all_reviews if r.order.status == 'cancelled'])
        refunded_reviews = len([r for r in all_reviews if r.order.status == 'refunded'])

        avg_rating = sum(r.rating for r in all_reviews if r.order.status in ['confirmed', 'completed'])
        avg_rating = avg_rating / (confirmed_reviews + completed_reviews) if (
                                                                                         confirmed_reviews + completed_reviews) > 0 else 0

        # Pagination
        paginator = Paginator(all_reviews, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'reviews': page_obj,
            'total_reviews': total_reviews,
            'confirmed_reviews': confirmed_reviews,
            'completed_reviews': completed_reviews,
            'pending_reviews': pending_reviews,
            'cancelled_reviews': cancelled_reviews,
            'refunded_reviews': refunded_reviews,
            'avg_rating': round(avg_rating, 1),
            'LANGUAGE_CODE': lang,
        }

    except Exception as e:
        messages.error(request, f"حدث خطأ أثناء استرجاع التقييمات: {str(e)}")
        return redirect('coachIndex')

    return render(request, 'coach_dashboard/reviews/coach_reviews.html', context)

@login_required
def product_service_reviews(request, item_type, item_id):
    """View all reviews for a specific product or service"""
    context = {}
    user = request.user
    lang = translation.get_language()

    try:
        # Verify coach access
        if not hasattr(user, 'userprofile') or not hasattr(user.userprofile, 'Coach_profile'):
            messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
            return redirect('home')

        # Get the item (product or service)
        if item_type == 'product':
            item = get_object_or_404(ProductsModel, id=item_id, creator=user)
            reviews = Review.objects.filter(product=item).select_related(
                'student', 'order', 'order_item'
            )
        elif item_type == 'service':
            item = get_object_or_404(ServicesModel, id=item_id, creator=user)
            reviews = Review.objects.filter(service=item).select_related(
                'student', 'order', 'order_item'
            )
        else:
            messages.error(request, "نوع العنصر غير صحيح.")
            return redirect('coach_reviews')

        # Calculate statistics
        total_reviews = reviews.count()
        avg_rating = reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating'] or 0
        rating_distribution = {
            5: reviews.filter(rating=5).count(),
            4: reviews.filter(rating=4).count(),
            3: reviews.filter(rating=3).count(),
            2: reviews.filter(rating=2).count(),
            1: reviews.filter(rating=1).count(),
        }

        # Status counts
        confirmed_reviews = reviews.filter(order__status='confirmed').count()
        completed_reviews = reviews.filter(order__status='completed').count()
        pending_reviews = reviews.filter(order__status='pending').count()
        cancelled_reviews = reviews.filter(order__status='cancelled').count()
        refunded_reviews = reviews.filter(order__status='refunded').count()

        context = {
            'item': item,
            'item_type': item_type,
            'reviews': reviews,
            'total_reviews': total_reviews,
            'avg_rating': round(avg_rating, 1),
            'rating_distribution': rating_distribution,
            'confirmed_reviews': confirmed_reviews,
            'completed_reviews': completed_reviews,
            'pending_reviews': pending_reviews,
            'cancelled_reviews': cancelled_reviews,
            'refunded_reviews': refunded_reviews,
            'LANGUAGE_CODE': lang,
        }

    except Exception as e:
        messages.error(request, f"حدث خطأ أثناء استرجاع التقييمات: {str(e)}")
        return redirect('coach_reviews')

    return render(request, 'coach_dashboard/reviews/item_reviews.html', context)

# views.py
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .forms import PolicyDocumentsForm

@login_required
def upload_policies(request):
    try:
        coach = request.user.userprofile.Coach_profile
    except AttributeError:
        messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return redirect('home')

    # If already approved, redirect to dashboard
    if coach.policies_approved:
        return redirect('coachIndex')

    if request.method == 'POST':
        form = PolicyDocumentsForm(request.POST, request.FILES, instance=coach)
        if form.is_valid():
            form.save()
            messages.success(request, "تم رفع الملفات بنجاح! يمكنك الآن إضافة منتجات وخدمات.")
            return redirect('coachIndex')
    else:
        form = PolicyDocumentsForm(instance=coach)

    context = {
        'form': form,
        'LANGUAGE_CODE': translation.get_language(),
        'club': getattr(coach, 'club', None),
    }
    return render(request, 'coach_dashboard/policies/upload_policies.html', context)

from django.core.exceptions import PermissionDenied
@login_required
def view_policies(request):
    try:
        coach = request.user.userprofile.Coach_profile
    except AttributeError:
        raise PermissionDenied("ليس لديك صلاحية للوصول إلى هذه الصفحة.")

    if not coach.policy_documents:
        messages.info(request, "لم يتم رفع أي ملفات سياسات بعد.")
        return redirect('upload_policies')

    context = {
        'coach': coach,
        'LANGUAGE_CODE': translation.get_language(),
        'club': getattr(coach, 'club', None),
    }
    return render(request, 'coach_dashboard/policies/view_policies.html', context)


@login_required
def edit_policies(request):
    try:
        coach = request.user.userprofile.Coach_profile
    except AttributeError:
        messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return redirect('home')

    if request.method == 'POST':
        form = PolicyDocumentsForm(request.POST, request.FILES, instance=coach)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث الملفات بنجاح!")
            return redirect('view_policies')
    else:
        form = PolicyDocumentsForm(instance=coach)

    context = {
        'form': form,
        'has_existing_policies': bool(coach.policy_documents),
        'LANGUAGE_CODE': translation.get_language(),
        'club': getattr(coach, 'club', None),
    }
    return render(request, 'coach_dashboard/policies/edit_policies.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CoachProfile, ReceptionistProfile, CoachReceptionistTicket, TicketMessage
from .forms import CoachTicketForm, TicketMessageForm


@login_required
def coach_ticket_list(request):
    user_profile = request.user.userprofile
    if user_profile.account_type != '4':  # 4 is coach
        return redirect('home')

    coach_profile = user_profile.Coach_profile
    tickets = CoachReceptionistTicket.objects.filter(coach=coach_profile).order_by('-created_at')
    return render(request, 'coach_dashboard/tickets/coach_ticket_list.html', {'tickets': tickets})



from django.db.models import Q
from datetime import timedelta

def get_available_receptionist(club):
    """Get the least recently assigned available receptionist"""
    now = timezone.now()

    # First try to find free receptionists who aren't on hold
    available = ReceptionistProfile.objects.filter(
        Q(club=club) & (Q(status='free') | Q(status='hold', hold_until__lt=now))
    ).order_by('last_assignment_time').first()

    return available




from django.db.models import Q, Count
from django.utils import timezone
from django.db.models import Q, Count
from django.utils import timezone

@login_required
def create_coach_ticket(request):
    user_profile = request.user.userprofile
    if user_profile.account_type != '4':
        return redirect('home')
    coach_profile = user_profile.Coach_profile
    if request.method == 'POST':
        form = CoachTicketForm(request.POST)
        if form.is_valid():
            # Find available receptionist with fewest closed tickets
            available_receptionists = ReceptionistProfile.objects.filter(
                club=coach_profile.club
            ).filter(
                Q(status='free') | Q(status='hold')
            ).annotate(
                closed_tickets_count=Count(
                    'received_tickets',
                    filter=Q(received_tickets__status='resolved') |
                           Q(received_tickets__status='closed')
                )
            ).order_by('closed_tickets_count', 'last_assignment_time')

            receptionist = available_receptionists.first() if available_receptionists.exists() else None

            # Create the ticket
            ticket = form.save(commit=False)
            ticket.coach = coach_profile

            if receptionist:
                ticket.assign_to_receptionist(receptionist)
                messages.success(request, "تم إنشاء طلب الدعم بنجاح وسيتم معالجته قريباً")
            else:
                ticket.status = 'pending'
                ticket.save()
                messages.success(request, "تم إنشاء طلب الدعم بنجاح وسيتم معالجته عند توفر موظف")

            return redirect('coach_ticket_list')
    else:
        form = CoachTicketForm()
    return render(request, 'coach_dashboard/tickets/create_coach_ticket.html', {'form': form})



@login_required
def resolve_ticket(request, ticket_id):
    ticket = get_object_or_404(CoachReceptionistTicket, id=ticket_id)


    # Verify permissions
    if request.user.userprofile.account_type == '4':  # Coach
        if ticket.coach != request.user.userprofile.Coach_profile:
            return HttpResponseForbidden("You don't have permission to resolve this ticket")
    elif request.user.userprofile.account_type == '5':  # Receptionist
        if ticket.receptionist != request.user.userprofile.receptionist_profile:
            return HttpResponseForbidden("You don't have permission to resolve this ticket")
    else:
        return redirect('home')

    ticket.mark_resolved()
    messages.success(request, "تم إغلاق التذكرة بنجاح")
    return redirect('coach_ticket_list' if request.user.userprofile.account_type == '4'
                    else 'receptionist_ticket_list')



@login_required
def set_receptionist_status(request):
    if request.method == 'POST' and request.user.userprofile.account_type == '5':
        status = request.POST.get('status')
        receptionist = request.user.userprofile.receptionist_profile

        if status == 'hold':
            receptionist.set_status('hold', 15)  # 15 minute hold
            messages.success(request, "You are now on hold for 15 minutes")
        elif status == 'free':
            receptionist.set_status('free')
            messages.success(request, "You are now available")

    return redirect('receptionist_ticket_list')





from django.db.models import Q, Count
from django.utils import timezone

@login_required
def assign_pending_tickets(request):
    """View for receptionists to manually claim pending tickets"""
    user_profile = request.user.userprofile
    if user_profile.account_type != '5':  # Only receptionists
        return redirect('home')

    receptionist = user_profile.receptionist_profile

    if not receptionist.is_available():
        messages.error(request, "You are not currently available to take new tickets")
        return redirect('receptionist_ticket_list')

    # Get oldest pending ticket for this club
    pending_ticket = CoachReceptionistTicket.objects.filter(
        status='pending',
        coach__club=receptionist.club
    ).order_by('created_at').first()

    if pending_ticket:
        # Find all available receptionists with their closed ticket counts
        available_receptionists = ReceptionistProfile.objects.filter(
            club=receptionist.club
        ).filter(
            Q(status='free') | Q(status='hold', hold_until__lt=timezone.now())
        ).annotate(
            closed_tickets_count=Count(
                'received_tickets',
                filter=Q(received_tickets__status='resolved') |
                       Q(received_tickets__status='closed')
            )
        ).order_by('closed_tickets_count', 'last_assignment_time')

        if available_receptionists.exists():
            # Assign to receptionist with fewest closed tickets (and oldest assignment if tie)
            best_receptionist = available_receptionists.first()
            pending_ticket.assign_to_receptionist(best_receptionist)

            if best_receptionist == receptionist:
                messages.success(request, f"تم تعيين التذكرة #{pending_ticket.id} إليك")
            else:
                messages.info(request, f"تم تعيين التذكرة #{pending_ticket.id} إلى {best_receptionist.full_name} (لديه أقل عدد من التذاكر المغلقة)")
        else:
            messages.error(request, "لا يوجد موظفين استقبال متاحين حالياً")
    else:
        messages.info(request, "لا توجد تذاكر معلقة حالياً")

    return redirect('receptionist_ticket_list')




@login_required
def coach_ticket_detail(request, ticket_id):
    user_profile = request.user.userprofile
    ticket = get_object_or_404(CoachReceptionistTicket, id=ticket_id)

    # Ensure the requesting user owns the ticket
    if user_profile.account_type == '4':  # Coach
        base_template = 'base_coach_dashboard.html'
        if ticket.coach != user_profile.Coach_profile:
            return redirect('coach_ticket_list')
    elif user_profile.account_type == '5':  # Receptionist
        base_template = 'base_receptionist_dashboard.html'
        if ticket.receptionist != user_profile.receptionist_profile:
            return redirect('receptionist_ticket_list')
    else:
        return redirect('home')

    if request.method == 'POST':
        form = TicketMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.ticket = ticket
            message.sender = user_profile
            message.save()

            # Update ticket status and read status
            if user_profile.account_type == '4':  # Coach
                ticket.is_read = False
            else:  # Receptionist
                ticket.is_read = True
                if ticket.status == 'open':
                    ticket.status = 'in_progress'
            ticket.save()

            return redirect('coach_ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketMessageForm()

    # Mark as read if receptionist is viewing
    if user_profile.account_type == '5' and not ticket.is_read:
        ticket.is_read = True
        ticket.save()

    messages = ticket.messages.all().order_by('created_at')
    return render(request, 'coach_dashboard/tickets/coach_ticket_detail.html', {
        'ticket': ticket,
        'messages': messages,
        'form': form,
        'base_template': base_template,
    })


# students/views.py
from django.db.models import Q
from club_dashboard.models import RefundStatus,RefundDispute

@login_required
def coach_refund_requests(request):
    """View for coaches to manage refund requests for their products/services"""
    user = request.user
    club = getattr(user.userprofile.Coach_profile, 'club', None) if hasattr(user, 'userprofile') else None

    # Get refund disputes where the coach is the creator of the product/service in the order item
    disputes = RefundDispute.objects.filter(
        Q(order_item__product__creator=user) |
        Q(order_item__service__coaches__userprofile__user=user),
        is_escalated=False
    ).distinct().order_by('-created_at')

    # Status counts
    status_counts = {
        'total': disputes.count(),
        'pending': disputes.filter(status=RefundStatus.PENDING).count(),
        'rejected': disputes.filter(status=RefundStatus.COACH_REJECTED).count(),
        'escalated': disputes.filter(status=RefundStatus.ESCALATED).count(),
    }

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter and status_filter in dict(RefundStatus.choices).keys():
        disputes = disputes.filter(status=status_filter)

    paginator = Paginator(disputes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'disputes': page_obj,
        'status_counts': status_counts,
        'status_filter': status_filter,
        'status_choices': RefundStatus.choices,
        'club': club,
    }
    return render(request, 'coach_dashboard/refunds/coach_refund_list.html', context)

from django.http import HttpResponseForbidden

from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils import timezone
from club_dashboard.models import RefundDispute, RefundDisputeMessage
from accounts.models import UserProfile


@login_required
def coach_refund_detail(request, dispute_id):
    dispute = get_object_or_404(RefundDispute, id=dispute_id)
    user_profile = request.user.userprofile

    # Verify coach has access
    if not (
            user_profile.account_type == '4' and
            (
                    (dispute.order_item.product and dispute.order_item.product.creator == request.user) or
                    (dispute.order_item.service and dispute.order_item.service.coaches.filter(
                        userprofile__user=request.user).exists())
            )
    ):
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

        elif action == 'approve':
            if dispute.current_stage == 'student_coach':
                dispute.status = RefundStatus.APPROVED
                dispute.approved_refund_amount = dispute.requested_refund_amount
                dispute.client_percentage = 100
                dispute.vendor_percentage = 0
                dispute.current_stage = 'resolved'
                dispute.resolved_at = timezone.now()
                dispute.save()
                messages.success(request, "Refund approved successfully")
            else:
                messages.error(request, "You can only approve in the initial stage")

        return redirect('coach_refund_detail', dispute_id=dispute.id)

    # Get all messages in the dispute
    conversation = dispute.messages.all().order_by('created_at')

    context = {
        'dispute': dispute,
        'order_item': dispute.order_item,
        'conversation': conversation,
        'can_approve': dispute.current_stage == 'student_coach',
        'can_message': dispute.current_stage in ['student_coach', 'receptionist', 'director'],
        'time_remaining': (dispute.next_escalation_time - timezone.now()) if dispute.next_escalation_time else None,
        'club': getattr(user_profile.Coach_profile, 'club', None),
    }
    return render(request, 'coach_dashboard/refunds/coach_refund_detail.html', context)


# In coach_dashboard/views.py
from django.contrib.contenttypes.models import ContentType


def send_coach_notification(coach, notification_type, message, related_object=None):
    """
    Send notification to a coach
    """
    notification = Notification.objects.create(
        club=coach,
        message=message,
        notification_type=notification_type,
        is_read=False
    )

    if related_object:
        notification.related_object_id = related_object.id
        notification.related_content_type = ContentType.objects.get_for_model(related_object).model
        notification.save()

    return notification


def notify_coach_for_order(order_item):
    """
    Notify coach when their product/service is ordered
    """
    if order_item.product and order_item.product.creator:
        coach = order_item.product.creator.userprofile.Coach_profile
        message = f"طلب جديد لمنتجك: {order_item.product.title} (الطلب رقم #{order_item.order.id})"
        send_coach_notification(coach, 'order', message, order_item.order)
    elif order_item.service:
        for coach in order_item.service.coaches.all():
            message = f"طلب جديد لخدمتك: {order_item.service.title} (الطلب رقم #{order_item.order.id})"
            send_coach_notification(coach, 'order', message, order_item.order)


def notify_coach_for_refund(refund_dispute):
    """
    Notify coach when refund is requested for their product/service
    """
    if refund_dispute.order_item.product and refund_dispute.order_item.product.creator:
        coach = refund_dispute.order_item.product.creator.userprofile.Coach_profile
        message = f"طلب استرداد أموال لمنتجك: {refund_dispute.order_item.product.title} (الطلب رقم #{refund_dispute.order_item.order.id})"
        send_coach_notification(coach, 'refund', message, refund_dispute)
    elif refund_dispute.order_item.service:
        for coach in refund_dispute.order_item.service.coaches.all():
            message = f"طلب استرداد أموال لخدمتك: {refund_dispute.order_item.service.title} (الطلب رقم #{refund_dispute.order_item.order.id})"
            send_coach_notification(coach, 'refund', message, refund_dispute)


def notify_coach_for_review(review):
    """
    Notify coach when their product/service gets a review
    """
    if review.product and review.product.creator:
        coach = review.product.creator.userprofile.Coach_profile
        message = f"تقييم جديد لمنتجك: {review.product.title} (التقييم: {review.rating}/5)"
        send_coach_notification(coach, 'review', message, review)
    elif review.service:
        for coach in review.service.coaches.all():
            message = f"تقييم جديد لخدمتك: {review.service.title} (التقييم: {review.rating}/5)"
            send_coach_notification(coach, 'review', message, review)


from django.db.models import Sum, Q, F
from decimal import Decimal


@login_required
def coach_financials(request):
    context = {}
    user = request.user

    try:
        coach_profile = user.userprofile.Coach_profile
    except AttributeError:
        context['error'] = "Coach profile not found"
        context['LANGUAGE_CODE'] = translation.get_language()
        return render(request, 'coach_dashboard/financials/viewCoachFinancials.html', context)

    club = getattr(coach_profile, 'club', None)

    # Get all order items that belong to this coach (either as product creator or service coach)
    order_items = OrderItem.objects.filter(
        Q(order__status__in=['paid', 'delivered', 'confirmed', 'completed']),
        Q(product__creator=user) | Q(service__creator=user)
    ).distinct()

    # Calculate revenues
    credit_card_items = order_items.filter(
        order__payment_method='credit_card'
    )
    cash_items = order_items.filter(
        order__payment_method='cash_on_delivery'
    )
    pending_items = order_items.filter(
        order__status='paid'
    )

    # Calculate vendor net profit for each category
    def calculate_vendor_net(items):
        total = Decimal('0.00')
        for item in items:
            if item.product:
                total += item.quantity * Decimal(str(item.product.vendor_net_profit))
            elif item.service:
                total += item.quantity * Decimal(str(item.service.vendor_net_profit))
        return total

    credit_card_revenue = calculate_vendor_net(credit_card_items)
    cash_revenue = calculate_vendor_net(cash_items)
    pending_revenue = calculate_vendor_net(pending_items)
    total_revenue = credit_card_revenue + cash_revenue

    # Get recent transactions (orders containing coach's items)
    recent_orders = Order.objects.filter(
        items__in=order_items
    ).distinct().order_by('-created_at')[:10]

    # Calculate monthly revenue (last 6 months)
    monthly_revenue = []
    for i in range(5, -1, -1):
        month = timezone.now() - timezone.timedelta(days=30 * i)
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)

        month_items = order_items.filter(
            order__created_at__range=[month_start, month_end]
        )
        revenue = calculate_vendor_net(month_items)

        monthly_revenue.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': revenue
        })

    # Prepare detailed transaction data for the table
    detailed_transactions = []
    for order in recent_orders:
        for item in order.items.filter(Q(product__creator=user) | Q(service__creator=user)):
            if item.product:
                product = item.product
                price = product.price
                tax = product.tax_authority_amount
                platform_fee = product.total_platform_fee
                net_profit = product.vendor_net_profit
                item_type = 'product'
                title = product.title
            elif item.service:
                service = item.service
                price = service.effective_price
                tax = service.tax_authority_amount
                platform_fee = service.total_platform_fee
                net_profit = service.vendor_net_profit
                item_type = 'service'
                title = service.title

            detailed_transactions.append({
                'order': order,
                'item': item,
                'type': item_type,
                'title': title,
                'quantity': item.quantity,
                'price': price,
                'tax': tax,
                'platform_fee': platform_fee,
                'net_profit': net_profit,
                'total_net_profit': net_profit * item.quantity
            })

    context = {
        'credit_card_revenue': credit_card_revenue,
        'cash_revenue': cash_revenue,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'recent_transactions': recent_orders,
        'detailed_transactions': detailed_transactions,
        'monthly_revenue': monthly_revenue,
        'club': club,
        'LANGUAGE_CODE': translation.get_language(),
    }

    return render(request, 'coach_dashboard/financials/viewCoachFinancials.html', context)


from django.db.models import Count,Max
from django.contrib.auth.models import User

@login_required
def coach_students(request):
    """View all students who ordered from this coach"""
    context = {}
    user = request.user

    # Verify coach access
    if not hasattr(user, 'userprofile') or not hasattr(user.userprofile, 'Coach_profile'):
        messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return redirect('home')

    coach = user.userprofile.Coach_profile
    club = getattr(coach, 'club', None)
    lang = translation.get_language()

    # Get students who ordered products created by this coach or services assigned to this coach
    students = User.objects.filter(
        Q(orders__items__product__creator=user) |
        Q(orders__items__service__coaches=coach)
    ).annotate(
        order_count=Count('orders', filter=Q(
            Q(orders__items__product__creator=user) |
            Q(orders__items__service__coaches=coach)
        )),
        last_order_date=Max('orders__created_at', filter=Q(
            Q(orders__items__product__creator=user) |
            Q(orders__items__service__coaches=coach)
        ))
    ).distinct().order_by('-last_order_date')

    # Filter by search query if provided
    search_query = request.GET.get('search')
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'students': page_obj,
        'search_query': search_query,
        'total_students': students.count(),
        'club': club,
        'LANGUAGE_CODE': lang,
    }

    return render(request, 'coach_dashboard/students/coach_students.html', context)


from coach_dashboard.forms import WorkingHoursForm
from coach_dashboard.forms import WorkingHoursForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone, translation
from datetime import datetime, time
import calendar


@login_required
def working_hours(request):
    try:
        coach = request.user.userprofile.Coach_profile
    except AttributeError:
        messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return redirect('home')

    # Calculate stats for the cards
    working_days = []
    total_hours = 0

    # Check each day if it's enabled and has valid hours
    for day, day_name in WorkingHoursForm.DAYS_OF_WEEK:
        day_data = coach.working_hours.get(day, {})

        # Check if day is enabled and has both opening and closing times
        if day_data.get('enabled', False) or (day_data.get('opening') and day_data.get('closing')):
            working_days.append(day)

            # Calculate hours for this day
            try:
                opening_str = day_data.get('opening', '09:00')
                closing_str = day_data.get('closing', '17:00')

                # Parse time strings
                opening = datetime.strptime(opening_str, '%H:%M').time()
                closing = datetime.strptime(closing_str, '%H:%M').time()

                # Calculate duration in hours
                opening_dt = datetime.combine(datetime.today(), opening)
                closing_dt = datetime.combine(datetime.today(), closing)

                # Handle case where closing time is next day (e.g., 23:00 to 02:00)
                if closing < opening:
                    closing_dt += timedelta(days=1)

                duration = closing_dt - opening_dt
                day_hours = duration.total_seconds() / 3600
                total_hours += day_hours

            except (ValueError, TypeError):
                # Skip days with invalid time format
                continue

    working_days_count = len(working_days)

    # Check if available today
    today = timezone.now().strftime('%A').lower()  # e.g., 'monday'
    today_data = coach.working_hours.get(today, {})
    is_available_today = (today_data.get('enabled', False) or
                          (today_data.get('opening') and today_data.get('closing')))

    # Calculate average hours per day
    average_hours_per_day = total_hours / working_days_count if working_days_count > 0 else 0

    if request.method == 'POST':
        form = WorkingHoursForm(request.POST, instance=coach)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث ساعات العمل بنجاح!")
            return redirect('working_hours')
    else:
        initial_data = {}
        for day, day_name in WorkingHoursForm.DAYS_OF_WEEK:
            day_data = coach.working_hours.get(day, {})
            # Fix: Check if day data exists and has required fields
            initial_data[f'{day}_enabled'] = (day_data.get('enabled', False) or
                                              (day_data.get('opening') and day_data.get('closing')))
            initial_data[f'{day}_opening'] = day_data.get('opening', '09:00')
            initial_data[f'{day}_closing'] = day_data.get('closing', '17:00')

        form = WorkingHoursForm(instance=coach, initial=initial_data)

    context = {
        'form': form,
        'coach': coach,
        'LANGUAGE_CODE': translation.get_language(),
        'club': getattr(coach, 'club', None),
        'working_days_count': working_days_count,
        'is_available_today': is_available_today,
        'average_hours_per_day': average_hours_per_day,
    }
    return render(request, 'coach_dashboard/working_hours/working_hours.html', context)


from students.models import ProductClick , ServiceClick
from django.db.models import Sum, Count, Q
from decimal import Decimal

@login_required
def coach_performance(request):
    context = {}
    user = request.user

    # Verify coach access
    if not hasattr(user, 'userprofile') or not hasattr(user.userprofile, 'Coach_profile'):
        messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return redirect('home')

    coach = user.userprofile.Coach_profile
    club = getattr(coach, 'club', None)
    lang = translation.get_language()

    # Get product click statistics for products created by this coach
    product_clicks = ProductClick.objects.filter(
        product__creator=user
    ).values('product__title', 'product__id').annotate(
        total_clicks=Count('id'),
        view_clicks=Count('id', filter=models.Q(source='view')),
        cart_clicks=Count('id', filter=models.Q(source='cart')),
        total_sales=Count('product__orderitem__order',
                          filter=models.Q(
                              product__orderitem__order__status__in=['paid', 'delivered', 'confirmed', 'completed']),
                          distinct=True),
        total_revenue=Sum('product__orderitem__price',
                          filter=models.Q(
                              product__orderitem__order__status__in=['paid', 'delivered', 'confirmed', 'completed']))
    ).order_by('-total_clicks')

    # Calculate total product clicks and sales
    total_product_clicks = sum(item['total_clicks'] for item in product_clicks)
    product_sales = sum(float(item['total_revenue'] or 0) for item in product_clicks)

    # Get service click statistics for services created by this coach
    service_clicks = ServiceClick.objects.filter(
        service__creator=user
    ).values('service__title', 'service__id').annotate(
        total_clicks=Count('id'),
        view_clicks=Count('id', filter=models.Q(source='view')),
        cart_clicks=Count('id', filter=models.Q(source='cart')),
        total_sales=Count('service__orderitem__order',
                          filter=models.Q(
                              service__orderitem__order__status__in=['paid', 'delivered', 'confirmed', 'completed']),
                          distinct=True),
        total_revenue=Sum('service__orderitem__price',
                          filter=models.Q(
                              service__orderitem__order__status__in=['paid', 'delivered', 'confirmed', 'completed']))
    ).order_by('-total_clicks')

    # Calculate total service clicks and sales
    total_service_clicks = sum(item['total_clicks'] for item in service_clicks)
    service_sales = sum(float(item['total_revenue'] or 0) for item in service_clicks)

    # Calculate view, cart and purchase rates
    total_clicks = total_product_clicks + total_service_clicks
    view_rate = 0
    cart_rate = 0
    purchase_rate = 0

    if total_clicks > 0:
        total_views = sum(item['view_clicks'] for item in product_clicks) + sum(
            item['view_clicks'] for item in service_clicks)
        total_carts = sum(item['cart_clicks'] for item in product_clicks) + sum(
            item['cart_clicks'] for item in service_clicks)
        view_rate = (total_views / total_clicks) * 100
        cart_rate = (total_carts / total_clicks) * 100

        # Calculate purchase rate (orders / total clicks)
        total_orders = Order.objects.filter(
            Q(items__product__creator=user) | Q(items__service__creator=user),
            status__in=['paid', 'delivered', 'confirmed', 'completed']
        ).count()
        purchase_rate = (total_orders / total_clicks) * 100 if total_clicks > 0 else 0

    # Get sales statistics
    orders = Order.objects.filter(
        Q(items__product__creator=user) | Q(items__service__creator=user),
        status__in=['paid', 'delivered', 'confirmed', 'completed']
    )

    total_sales = orders.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    total_orders_count = orders.count()
    avg_order_value = total_sales / total_orders_count if total_orders_count > 0 else Decimal('0.00')

    # Get repeat customers (students who ordered more than once)
    repeat_customers = User.objects.filter(
        Q(orders__items__product__creator=user) | Q(orders__items__service__creator=user)
    ).annotate(order_count=Count('orders')).filter(order_count__gt=1).count()

    # Get recent orders
    recent_orders = orders.order_by('-created_at')[:5]

    daily_sales = []
    for i in range(29, -1, -1):
        day = timezone.now() - timezone.timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

        sales = orders.filter(
            created_at__range=[day_start, day_end],
            status__in=['paid', 'delivered', 'confirmed', 'completed']
        ).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')

        daily_sales.append({
            'date': day.strftime('%Y-%m-%d'),
            'sales': sales,
            'day_name': day.strftime('%a')  # Short day name
        })

    # Calculate weekly sales for the last 12 weeks
    weekly_sales = []
    for i in range(11, -1, -1):
        week_start = timezone.now() - timezone.timedelta(weeks=i + 1)
        week_start = week_start - timezone.timedelta(days=week_start.weekday())  # Start of week (Monday)
        week_end = week_start + timezone.timedelta(days=6)

        sales = orders.filter(
            created_at__range=[week_start, week_end],
            status__in=['paid', 'delivered', 'confirmed', 'completed']
        ).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')

        weekly_sales.append({
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'sales': sales,
            'week_number': week_start.isocalendar()[1]
        })

    # Calculate monthly sales for the last 12 months
    monthly_sales = []
    for i in range(11, -1, -1):
        month = timezone.now() - timezone.timedelta(days=30 * i)
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)

        sales = orders.filter(
            created_at__range=[month_start, month_end],
            status__in=['paid', 'delivered', 'confirmed', 'completed']
        ).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')

        monthly_sales.append({
            'month': month_start.strftime('%Y-%m'),
            'sales': sales,
            'month_name': month_start.strftime('%b %Y')
        })

    context = {
        'product_clicks': product_clicks,
        'service_clicks': service_clicks,
        'total_clicks': total_clicks,
        'view_rate': view_rate,
        'cart_rate': cart_rate,
        'purchase_rate': purchase_rate,
        'total_sales': total_sales,
        'product_sales': product_sales,
        'service_sales': service_sales,
        'total_orders': total_orders_count,
        'avg_order_value': avg_order_value,
        'repeat_customers': repeat_customers,
        'daily_sales': daily_sales,
        'weekly_sales': weekly_sales,
        'monthly_sales': monthly_sales,
        'recent_orders': recent_orders,
        'club': club,
        'LANGUAGE_CODE': lang,
    }
    return render(request, 'coach_dashboard/performance/coach_performance.html', context)


from django.db.models import Sum, Q, F, Count
from decimal import Decimal
from django.template.loader import render_to_string
from django.http import HttpResponse
import tempfile
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.utils import translation


@login_required
def coach_payments(request):
    """View for coaches to review their payments and invoices"""
    context = {}
    user = request.user
    coach_profile = user.userprofile.Coach_profile
    club = getattr(coach_profile, 'club', None)

    # Get all orders where coach is the creator of products or services
    orders = Order.objects.filter(
        Q(items__product__creator=user) | Q(items__service__creator=user)
    ).distinct().order_by('-created_at')

    def calculate_item_total(item):
        """Calculate total for an item considering discounted price if available"""
        if item.product:
            return item.price * item.quantity
        elif item.service:
            # Use discounted price if available, otherwise regular price
            effective_price = item.service.discounted_price if item.service.discounted_price else item.price
            return Decimal(str(effective_price)) * Decimal(str(item.quantity))
        return Decimal('0.00')

    # Initialize earnings with all possible statuses
    earnings = {
        'pending': Decimal('0.00'),
        'paid': Decimal('0.00'),
        'confirmed': Decimal('0.00'),
        'completed': Decimal('0.00'),
        'cancelled': Decimal('0.00'),
        'delivered': Decimal('0.00'),
    }

    for order in orders:
        for item in order.items.all():
            if (item.product and item.product.creator == user) or (item.service and item.service.creator == user):
                item_total = calculate_item_total(item)
                # Safely add to the earnings dictionary
                earnings[order.status] = earnings.get(order.status, Decimal('0.00')) + item_total

    # Total earnings (confirmed + completed)
    total_earnings = earnings['confirmed'] + earnings['completed']

    # Group by month for earnings chart
    monthly_earnings = []
    for i in range(11, -1, -1):
        month = timezone.now() - timedelta(days=30 * i)
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        month_earnings = Decimal('0.00')
        month_orders = orders.filter(
            created_at__range=[month_start, month_end],
            status__in=['confirmed', 'completed']
        )

        for order in month_orders:
            for item in order.items.all():
                if (item.product and item.product.creator == user) or (item.service and item.service.creator == user):
                    month_earnings += calculate_item_total(item)

        monthly_earnings.append({
            'month': month_start.strftime('%b %Y'),
            'earnings': float(month_earnings)
        })

    # Filter by date range if requested
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    filtered_orders = orders

    if date_from and date_to:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            date_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            filtered_orders = orders.filter(
                created_at__range=[date_from, date_to]
            )
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")

    # Pagination
    paginator = Paginator(filtered_orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'total_earnings': total_earnings,
        'pending_earnings': earnings['pending'],
        'paid_earnings': earnings['paid'],
        'confirmed_earnings': earnings['confirmed'],
        'completed_earnings': earnings['completed'],
        'monthly_earnings': monthly_earnings,
        'date_from': date_from.strftime('%Y-%m-%d') if date_from else '',
        'date_to': date_to.strftime('%Y-%m-%d') if date_to else '',
        'club': club,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/payments/coach_payments.html', context)



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Promotion, PromotionFeature
from students.models import ProductsModel, ServicesModel
from accounts.models import CoachProfile


@login_required
def coach_marketing_dashboard(request):
    """Marketing dashboard for coaches"""
    user = request.user
    user_profile = user.userprofile

    if not hasattr(user_profile, 'Coach_profile'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')

    coach = user_profile.Coach_profile
    club = coach.club

    # Get coach's products and services
    products = ProductsModel.objects.filter(club=club, creator=user, approval_status='approved')
    services = ServicesModel.objects.filter(club=club, creator=user, approval_status='approved')

    # Get coach's promotions
    promotions = Promotion.objects.filter(coach=coach).order_by('-created_at')
    active_promotions = promotions.filter(status='active')
    pending_promotions = promotions.filter(status='pending')

    # Get available promotion features for this club
    features = PromotionFeature.objects.filter(club=club, is_active=True)

    context = {
        'coach': coach,
        'club': club,
        'products': products,
        'services': services,
        'promotions': promotions,
        'active_promotions': active_promotions,
        'pending_promotions': pending_promotions,
        'features': features,
        'base_price_per_day': club.promotion_base_price or 100,
    }
    return render(request, 'coach_dashboard/marketing/marketing_dashboard.html', context)


@login_required
def create_promotion(request):
    """Create a new promotion with selected features"""
    user = request.user
    user_profile = user.userprofile

    print("User:", user.username)

    if not hasattr(user_profile, 'Coach_profile'):
        messages.error(request, "You don't have permission to perform this action.")
        print("User does not have a Coach_profile.")
        return redirect('home')

    coach = user_profile.Coach_profile
    club = coach.club

    print("Club:", club.name)

    if request.method == 'POST':
        promotion_type = request.POST.get('promotion_type')
        item_id = request.POST.get('item_id')
        duration_days = int(request.POST.get('duration_days', 1))
        feature_ids = request.POST.getlist('features')
        base_price_per_day = float(club.promotion_base_price or 10)

        print("Received POST data:")
        print("Promotion Type:", promotion_type)
        print("Item ID:", item_id)
        print("Duration Days:", duration_days)
        print("Feature IDs:", feature_ids)
        print("Base Price Per Day:", base_price_per_day)

        try:
            # Create the promotion object but don't save yet
            promotion = Promotion(
                coach=coach,
                promotion_type=promotion_type,
                duration_days=duration_days,
                base_price_per_day=base_price_per_day,
                status='pending'
            )

            # Set product or service before saving
            if promotion_type == 'product':
                product = ProductsModel.objects.get(id=item_id, club=club, creator=user)
                promotion.product = product
                print("Product assigned:", product.title)
            else:
                service = ServicesModel.objects.get(id=item_id, club=club, creator=user)
                promotion.service = service
                print("Service assigned:", service.title)

            # Now save the promotion to get an ID
            promotion.save()
            print("Promotion created with ID:", promotion.id)

            # Now we can set the M2M features since the promotion has an ID
            if feature_ids:
                features = PromotionFeature.objects.filter(id__in=feature_ids, club=club)
                promotion.features.set(features)
                print("Features set:", [f.name for f in features])

                # Recalculate price after setting features
                promotion.calculate_price()
                promotion.save()

            print("Final promotion details - Total price:", promotion.total_price)

            messages.success(request,
                             f"Promotion request submitted successfully! Total cost: {promotion.total_price} {club.vat_settings.currency}")

        except ProductsModel.DoesNotExist:
            print("Product not found or doesn't belong to user/club")
            messages.error(request, "Selected product not found or you don't have permission to promote it.")
        except ServicesModel.DoesNotExist:
            print("Service not found or doesn't belong to user/club")
            messages.error(request, "Selected service not found or you don't have permission to promote it.")
        except Exception as e:
            print("Exception occurred while creating promotion:", str(e))
            messages.error(request, f"Error creating promotion: {str(e)}")

    return redirect('coach_marketing')




@login_required
def get_promotion_price(request):
    """Calculate promotion price based on selected features"""
    user = request.user
    user_profile = user.userprofile

    if not hasattr(user_profile, 'Coach_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    club = user_profile.Coach_profile.club
    duration_days = int(request.GET.get('duration_days', 1))
    feature_ids = request.GET.getlist('features[]', [])

    base_price = club.promotion_base_price or 10
    multiplier = 1.0

    if feature_ids:
        features = PromotionFeature.objects.filter(id__in=feature_ids, club=club)
        for feature in features:
            multiplier *= feature.price_multiplier

    total_price = base_price * duration_days * multiplier

    return JsonResponse({
        'base_price': base_price,
        'duration_days': duration_days,
        'multiplier': multiplier,
        'total_price': total_price,
        'currency': club.vat_settings.currency
    })




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import translation
from .models import Coupon, CouponUsage
from .forms import CouponForm
from accounts.models import CoachProfile


@login_required
def coach_coupons(request):
    """View all coupons for a coach"""
    context = {}
    user = request.user
    coach = user.userprofile.Coach_profile
    club = getattr(coach, 'club', None)

    coupons = Coupon.objects.filter(coach=coach).order_by('-created_at')

    # Calculate stats for the cards
    active_coupons = coupons.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).count()

    upcoming_coupons = coupons.filter(
        is_active=True,
        start_date__gt=timezone.now()
    ).count()

    expired_coupons = coupons.filter(
        end_date__lt=timezone.now()
    ).count()

    inactive_coupons = coupons.filter(
        is_active=False
    ).count()

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        coupons = coupons.filter(is_active=True, start_date__lte=timezone.now(), end_date__gte=timezone.now())
    elif status_filter == 'upcoming':
        coupons = coupons.filter(is_active=True, start_date__gt=timezone.now())
    elif status_filter == 'expired':
        coupons = coupons.filter(end_date__lt=timezone.now())
    elif status_filter == 'inactive':
        coupons = coupons.filter(is_active=False)

    context = {
        'coupons': coupons,
        'status_filter': status_filter,
        'club': club,
        'active_coupons': active_coupons,
        'upcoming_coupons': upcoming_coupons,
        'expired_coupons': expired_coupons,
        'inactive_coupons': inactive_coupons,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/coupons/coupon_list.html', context)


@login_required
def add_coupon(request):
    """Add a new coupon"""
    context = {}
    user = request.user
    coach = user.userprofile.Coach_profile
    club = getattr(coach, 'club', None)

    if request.method == 'POST':
        form = CouponForm(request.POST, coach=coach)

        # Debug: Print form data
        print("Form data:", request.POST)
        print("Form is valid:", form.is_valid())

        if not form.is_valid():
            print("Form errors:", form.errors)
            print("Non-field errors:", form.non_field_errors())

        if form.is_valid():
            try:
                coupon = form.save(commit=False)
                coupon.coach = coach
                coupon.save()
                form.save_m2m()  # Save many-to-many relationships

                print(f"Coupon created successfully: {coupon.id}")
                messages.success(request, "Coupon created successfully!")
                return redirect('coach_coupons')
            except Exception as e:
                print(f"Error saving coupon: {e}")
                messages.error(request, f"Error creating coupon: {e}")
    else:
        form = CouponForm(coach=coach)

    context = {
        'form': form,
        'club': club,
        'title': 'Add Coupon'  # Add this for the template
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/coupons/add_coupon.html', context)


@login_required
def edit_coupon(request, coupon_id):
    """Edit an existing coupon"""
    context = {}
    user = request.user
    coach = user.userprofile.Coach_profile
    club = getattr(coach, 'club', None)

    coupon = get_object_or_404(Coupon, id=coupon_id, coach=coach)

    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon, coach=coach)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon updated successfully!")
            return redirect('coach_coupons')
    else:
        form = CouponForm(instance=coupon, coach=coach)

    context = {
        'form': form,
        'coupon': coupon,
        'club': club,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/coupons/edit_coupon.html', context)


@login_required
def toggle_coupon_status(request, coupon_id):
    """Toggle coupon active status"""
    user = request.user
    coupon = get_object_or_404(Coupon, id=coupon_id, coach=user.userprofile.Coach_profile)

    coupon.is_active = not coupon.is_active
    coupon.save()

    status = "activated" if coupon.is_active else "deactivated"
    messages.success(request, f"Coupon has been {status}")
    return redirect('coach_coupons')


@login_required
def delete_coupon(request, coupon_id):
    """Delete a coupon"""
    user = request.user
    coupon = get_object_or_404(Coupon, id=coupon_id, coach=user.userprofile.Coach_profile)

    coupon.delete()
    messages.success(request, "Coupon deleted successfully!")
    return redirect('coach_coupons')


@login_required
def coupon_usage(request, coupon_id):
    """View usage history for a coupon"""
    context = {}
    user = request.user
    coach = user.userprofile.Coach_profile
    club = getattr(coach, 'club', None)

    coupon = get_object_or_404(Coupon, id=coupon_id, coach=coach)
    usages = CouponUsage.objects.filter(coupon=coupon).order_by('-used_at')

    context = {
        'coupon': coupon,
        'usages': usages,
        'club': club,
    }
    context['LANGUAGE_CODE'] = translation.get_language()
    return render(request, 'coach_dashboard/coupons/coupon_usage.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import VendorWorkingHours
from .forms import VendorWorkingHoursForm
from django.utils import timezone


@login_required
def vendor_working_hours_list(request):
    coach = request.user.userprofile.Coach_profile
    working_hours = VendorWorkingHours.objects.filter(coach=coach).order_by('-is_active', '-start_date')

    # Get current schedule if exists
    current_schedule = working_hours.filter(
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date(),
        is_active=True
    ).first()

    context = {
        'working_hours': working_hours,
        'current_schedule': current_schedule,
        'club': getattr(coach, 'club', None),
        'LANGUAGE_CODE': translation.get_language(),
    }
    return render(request, 'coach_dashboard/vendor_working_hours/vendor_working_hours_list.html', context)


@login_required
def add_vendor_working_hours(request):
    coach = request.user.userprofile.Coach_profile

    if request.method == 'POST':
        form = VendorWorkingHoursForm(request.POST)
        if form.is_valid():
            working_hours = form.save(commit=False)
            working_hours.coach = coach

            # Only allow one active schedule at a time
            if working_hours.is_active:
                VendorWorkingHours.objects.filter(coach=coach, is_active=True).update(is_active=False)

            working_hours.save()
            messages.success(request, "Working hours schedule added successfully!")
            return redirect('vendor_working_hours_list')
    else:
        # Set default start date to today and end date to 3 months from now
        today = timezone.now().date()
        default_end = today + timezone.timedelta(days=90)
        form = VendorWorkingHoursForm(initial={
            'start_date': today,
            'end_date': default_end
        })

    context = {
        'form': form,
        'club': getattr(coach, 'club', None),
        'LANGUAGE_CODE': translation.get_language(),
    }
    return render(request, 'coach_dashboard/vendor_working_hours/add_vendor_working_hours.html', context)


@login_required
def edit_vendor_working_hours(request, pk):
    coach = request.user.userprofile.Coach_profile
    working_hours = get_object_or_404(VendorWorkingHours, pk=pk, coach=coach)

    if request.method == 'POST':
        form = VendorWorkingHoursForm(request.POST, instance=working_hours)
        if form.is_valid():
            updated_hours = form.save(commit=False)

            # Only allow one active schedule at a time
            if updated_hours.is_active:
                VendorWorkingHours.objects.filter(coach=coach, is_active=True).exclude(pk=pk).update(is_active=False)

            updated_hours.save()
            messages.success(request, "Working hours schedule updated successfully!")
            return redirect('vendor_working_hours_list')
    else:
        form = VendorWorkingHoursForm(instance=working_hours)

    context = {
        'form': form,
        'working_hours': working_hours,
        'club': getattr(coach, 'club', None),
        'LANGUAGE_CODE': translation.get_language(),
    }
    return render(request, 'coach_dashboard/vendor_working_hours/edit_vendor_working_hours.html', context)


@login_required
def toggle_vendor_working_hours(request, pk):
    coach = request.user.userprofile.Coach_profile
    working_hours = get_object_or_404(VendorWorkingHours, pk=pk, coach=coach)

    if working_hours.is_active:
        working_hours.is_active = False
        working_hours.save()
        messages.success(request, "Schedule deactivated successfully!")
    else:
        # Deactivate all other active schedules first
        VendorWorkingHours.objects.filter(coach=coach, is_active=True).update(is_active=False)
        working_hours.is_active = True
        working_hours.save()
        messages.success(request, "Schedule activated successfully!")

    return redirect('vendor_working_hours_list')


@login_required
def delete_vendor_working_hours(request, pk):
    coach = request.user.userprofile.Coach_profile
    working_hours = get_object_or_404(VendorWorkingHours, pk=pk, coach=coach)
    working_hours.delete()
    messages.success(request, "Schedule deleted successfully!")
    return redirect('vendor_working_hours_list')