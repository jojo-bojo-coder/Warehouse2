from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
from accounts.models import AccountantProfile,CoachProfile
from students.models import Order
from django.utils import translation
from django.db.models.functions import TruncDay

import json
@login_required
def accountant_dashboard(request):
    # Verify user is an accountant
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    club = accountant_profile.club

    # Date range for reports (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    # Revenue data
    revenue = (
        Order.objects.filter(
            club=club,
            status__in=['confirmed', 'completed'],
            created_at__range=[start_date, end_date]
        )
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total=Sum('total_price'))
        .order_by('day')
    )

    # Financial summary
    total_revenue = Order.objects.filter(
        club=club,
        status__in=['confirmed', 'completed'],
        created_at__range=[start_date, end_date]
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # Expenses (simplified - in real app this would come from expense model)
    total_expenses = Order.objects.filter(
        club=club,
        status='cancelled',
        created_at__range=[start_date, end_date]
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # Net profit
    net_profit = total_revenue - total_expenses

    # Pending transactions
    pending_transactions_count = Order.objects.filter(
        club=club,
        status='pending',
        created_at__range=[start_date, end_date]
    ).count()

    # Recent transactions (last 10 orders)
    recent_transactions = Order.objects.filter(
        club=club,
        created_at__range=[start_date, end_date]
    ).order_by('-created_at')[:10]

    # Expense breakdown by category (simplified example)
    expense_breakdown = (
        Order.objects.filter(
            club=club,
            status='cancelled',
            created_at__range=[start_date, end_date]
        )
        .annotate(
            category_name_ar=Case(
                When(items__product__isnull=False,
                     then=F('items__product__creator__userprofile__Coach_profile__activity_type__name_ar')),
                When(items__service__isnull=False,
                     then=F('items__service__creator__userprofile__Coach_profile__activity_type__name_ar')),
                output_field=models.CharField()
            )
        )
        .values('category_name_ar')
        .annotate(total=Sum('total_price'))
        .filter(category_name_ar__isnull=False)
        .order_by('-total')
    )

    # Prepare chart data
    revenue_dates = [entry['day'].strftime('%Y-%m-%d') for entry in revenue]
    revenue_amounts = [float(entry['total']) for entry in revenue]

    expense_categories = [entry['category_name'] for entry in expense_breakdown]
    expense_amounts = [float(entry['total']) for entry in expense_breakdown]

    context = {
        'club': club,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'pending_transactions_count': pending_transactions_count,
        'recent_transactions': recent_transactions,
        'revenue_dates': json.dumps(revenue_dates),
        'revenue_amounts': json.dumps(revenue_amounts),
        'expense_categories': json.dumps(expense_categories),
        'expense_amounts': json.dumps(expense_amounts),
        'LANGUAGE_CODE': translation.get_language(),
    }

    return render(request, 'accountant_dashboard/index.html', context)

from club_dashboard.models import Category
from django.db.models import Q,F
from django.db.models import Case,When
from django.db import models


@login_required
def revenue_analytics(request):
    # Verify user is an accountant
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    club = accountant_profile.club

    time_period = request.GET.get('period', '30d')
    category_id = request.GET.get('category')
    coach_id = request.GET.get('coach')
    region = request.GET.get('region')

    end_date = timezone.now()
    if time_period == '7d':
        start_date = end_date - timedelta(days=7)
    elif time_period == '30d':
        start_date = end_date - timedelta(days=30)
    elif time_period == '90d':
        start_date = end_date - timedelta(days=90)
    elif time_period == '12m':
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)
        time_period = '30d'

    orders = Order.objects.filter(
        club=club,
        status__in=['confirmed', 'completed'],
        created_at__range=[start_date, end_date]
    )

    if category_id:
        orders = orders.filter(
            Q(items__product__creator__userprofile__Coach_profile__activity_type__id=category_id) |
            Q(items__service__creator__userprofile__Coach_profile__activity_type__id=category_id)
        ).distinct()

    if coach_id:
        orders = orders.filter(
            Q(items__product__creator__userprofile__Coach_profile__id=coach_id) |
            Q(items__service__creator__userprofile__Coach_profile__id=coach_id)
        ).distinct()

    if region:
        orders = orders.filter(
            Q(items__product__creator__userprofile__Coach_profile__region=region) |
            Q(items__service__creator__userprofile__Coach_profile__region=region)
        ).distinct()

    revenue_by_day = (
        orders.annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total=Sum('total_price'))
        .order_by('day')
    )

    revenue_by_category = (
        orders.annotate(
            category_id=Case(
                When(items__product__isnull=False,
                     then=F('items__product__creator__userprofile__Coach_profile__activity_type__id')),
                When(items__service__isnull=False,
                     then=F('items__service__creator__userprofile__Coach_profile__activity_type__id')),
                output_field=models.IntegerField()
            ),
            category_name_ar=Case(
                When(items__product__isnull=False,
                     then=F('items__product__creator__userprofile__Coach_profile__activity_type__name_ar')),
                When(items__service__isnull=False,
                     then=F('items__service__creator__userprofile__Coach_profile__activity_type__name_ar')),
                output_field=models.CharField()
            )
        )
        .values('category_id', 'category_name_ar')
        .annotate(total=Sum('total_price'))
        .filter(category_name_ar__isnull=False)
        .order_by('-total')
    )

    revenue_by_coach = (
        orders.annotate(
            coach_id=Case(
                When(items__product__isnull=False,
                     then=F('items__product__creator__userprofile__Coach_profile__id')),
                When(items__service__isnull=False,
                     then=F('items__service__creator__userprofile__Coach_profile__id')),
                output_field=models.IntegerField()
            ),
            coach_name=Case(
                When(items__product__isnull=False,
                     then=F('items__product__creator__userprofile__Coach_profile__full_name')),
                When(items__service__isnull=False,
                     then=F('items__service__creator__userprofile__Coach_profile__full_name')),
                output_field=models.CharField()
            )
        )
        .values('coach_id', 'coach_name')
        .annotate(total=Sum('total_price'))
        .filter(coach_name__isnull=False)
        .order_by('-total')
    )

    revenue_by_region = (
        orders.annotate(
            region_name=Case(
                When(items__product__isnull=False,
                     then=F('items__product__creator__userprofile__Coach_profile__region')),
                When(items__service__isnull=False,
                     then=F('items__service__creator__userprofile__Coach_profile__region')),
                output_field=models.CharField()
            )
        )
        .values('region_name')
        .annotate(total=Sum('total_price'))
        .filter(region_name__isnull=False)
        .order_by('-total')
    )

    categories = Category.objects.filter(
        id__in=CoachProfile.objects.filter(club=club).values_list('activity_type', flat=True).distinct()
    )

    coaches = CoachProfile.objects.filter(club=club)

    regions = CoachProfile.objects.filter(club=club).values_list('region', flat=True).distinct()

    import json

    revenue_dates = [entry['day'].strftime('%Y-%m-%d') for entry in revenue_by_day]
    revenue_amounts = [float(entry['total']) for entry in revenue_by_day]

    category_labels = [entry['category_name_ar'] or 'Unknown' for entry in revenue_by_category[:5]]
    category_data = [float(entry['total']) for entry in revenue_by_category[:5]]

    coach_labels = [entry['coach_name'] or 'Unknown' for entry in revenue_by_coach[:5]]
    coach_data = [float(entry['total']) for entry in revenue_by_coach[:5]]

    region_labels = [entry['region_name'] or 'Unknown' for entry in revenue_by_region[:5]]
    region_data = [float(entry['total']) for entry in revenue_by_region[:5]]

    category_comparison = []
    if len(revenue_by_category) > 1:
        sorted_categories = sorted(revenue_by_category, key=lambda x: x['total'], reverse=True)

        top_category = sorted_categories[0]
        bottom_category = sorted_categories[-1]

        difference = top_category['total'] - bottom_category['total']
        percentage_diff = (difference / bottom_category['total']) * 100 if bottom_category['total'] > 0 else 100

        category_comparison = {
            'top_category': top_category,
            'bottom_category': bottom_category,
            'difference': difference,
            'percentage_diff': percentage_diff,
        }

    refund_rates = (
        Order.objects.filter(
            club=club,
            created_at__range=[start_date, end_date]
        )
        .annotate(
            category_id=Case(
                When(items__product__isnull=False,
                     then=F('items__product__creator__userprofile__Coach_profile__activity_type__id')),
                When(items__service__isnull=False,
                     then=F('items__service__creator__userprofile__Coach_profile__activity_type__id')),
                output_field=models.IntegerField()
            ),
            category_name_ar=Case(
                When(items__product__isnull=False,
                     then=F('items__product__creator__userprofile__Coach_profile__activity_type__name_ar')),
                When(items__service__isnull=False,
                     then=F('items__service__creator__userprofile__Coach_profile__activity_type__name_ar')),
                output_field=models.CharField()
            )
        )
        .values('category_id', 'category_name_ar')
        .annotate(
            total_orders=Count('id'),
            refunded_orders=Count('id', filter=Q(status='cancelled')),
        )
        .annotate(
            refund_rate=Case(
                When(total_orders=0, then=0.0),
                default=F('refunded_orders') * 1.0 / F('total_orders') * 100,
                output_field=models.FloatField()
            )
        )
        .filter(category_name_ar__isnull=False)
        .order_by('-refund_rate')
    )

    high_refund_categories = [entry for entry in refund_rates if entry['refund_rate'] > 10]

    context = {
        'club': club,
        'time_period': time_period,
        'category_comparison': category_comparison,
        'selected_category': category_id,
        'selected_coach': coach_id,
        'selected_region': region,
        'categories': categories,
        'coaches': coaches,
        'regions': regions,
        'refund_rates': refund_rates,
        'high_refund_categories': high_refund_categories,
        'revenue_dates': json.dumps(revenue_dates),
        'revenue_amounts': json.dumps(revenue_amounts),
        'revenue_by_category': revenue_by_category,
        'revenue_by_coach': revenue_by_coach,
        'revenue_by_region': revenue_by_region,
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'coach_labels': json.dumps(coach_labels),
        'coach_data': json.dumps(coach_data),
        'region_labels': json.dumps(region_labels),
        'region_data': json.dumps(region_data),
        'total_revenue': orders.aggregate(total=Sum('total_price'))['total'] or 0,
        'LANGUAGE_CODE': translation.get_language(),
    }

    return render(request, 'accountant_dashboard/revenue_analytics.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import VATSettingsForm
from .models import VATSettings
from django.conf import settings

@login_required
def vat_settings(request):
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    club = accountant_profile.club

    try:
        vat_settings = VATSettings.objects.get(club=club)
    except VATSettings.DoesNotExist:
        vat_settings = VATSettings.objects.create(club=club)

    if request.method == 'POST':
        form = VATSettingsForm(request.POST, instance=vat_settings, language=request.LANGUAGE_CODE)
        if form.is_valid():
            # Save the form data
            saved_settings = form.save()

            # Handle language change
            language = form.cleaned_data.get('language')
            if language and language != request.LANGUAGE_CODE:
                translation.activate(language)
                response = redirect('accountant_vat_settings')
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
                messages.success(request, "Settings updated successfully")
                return response

            messages.success(request, "VAT settings updated successfully")
            return redirect('accountant_vat_settings')
        else:
            # Add error message if form is not valid
            messages.error(request, "Please correct the errors below.")
    else:
        form = VATSettingsForm(instance=vat_settings, language=request.LANGUAGE_CODE)

    context = {
        'club': club,
        'form': form,
        'LANGUAGE_CODE': translation.get_language(),
    }
    return render(request, 'accountant_dashboard/vat_settings.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from students.models import Order
from .models import BillRevision, BillRevisionComment
from .forms import BillRevisionForm, BillRevisionCommentForm
from django.utils import translation


@login_required
def accountant_bills_review(request):
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    club = accountant_profile.club

    orders = Order.objects.filter(
        club=club,
        status__in=['confirmed', 'completed']
    ).prefetch_related('bill_revisions')

    revisions = BillRevision.objects.filter(
        order__club=club,
        status__in=['pending', 'accountant_reviewed']
    ).select_related('order', 'order__user')

    context = {
        'club': club,
        'orders': orders,
        'revisions': revisions,
        'LANGUAGE_CODE': translation.get_language()
    }
    return render(request, 'accountant_dashboard/bills/bills_review.html', context)


from django.utils import translation
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BillRevision, BillRevisionComment
from .forms import BillRevisionForm, BillRevisionCommentForm
from students.models import Order


@login_required
def accountant_review_bill(request, order_id):
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    order = get_object_or_404(Order, id=order_id, club=request.user.userprofile.accountant_profile.club)
    revision, created = BillRevision.objects.get_or_create(
        order=order,
        defaults={
            'accountant': request.user.userprofile,
            'status': 'pending'
        }
    )

    if request.method == 'POST':
        form = BillRevisionForm(request.POST, instance=revision)
        comment_form = BillRevisionCommentForm(request.POST)

        if form.is_valid():
            revision = form.save(commit=False)
            revision.status = 'accountant_reviewed'
            revision.save()

            if comment_form.is_valid() and comment_form.cleaned_data.get('comment'):
                BillRevisionComment.objects.create(
                    revision=revision,
                    author=request.user.userprofile,
                    comment=comment_form.cleaned_data['comment']
                )

            messages.success(request, "Bill revision submitted successfully")
            return redirect('accountant_bills_review')
        else:
            # Add debug logging for form errors
            print("Form errors:", form.errors)
            messages.error(request, "Please correct the errors below")
    else:
        form = BillRevisionForm(instance=revision)
        comment_form = BillRevisionCommentForm()

    context = {
        'club': request.user.userprofile.accountant_profile.club,
        'order': order,
        'revision': revision,
        'form': form,
        'comment_form': comment_form,
        'comments': revision.comments.all().select_related('author'),
        'LANGUAGE_CODE': translation.get_language()
    }
    return render(request, 'accountant_dashboard/bills/review_bill.html', context)


from django.http import HttpResponse
from django.shortcuts import render
import csv
from datetime import datetime
from django.utils import timezone
from students.models import Order, OrderItem
from accounts.models import CoachProfile


@login_required
def custom_financial_reports(request):
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    club = accountant_profile.club

    # Get filter parameters
    report_type = request.GET.get('report_type', 'products')
    period = request.GET.get('period', '30d')
    coach_id = request.GET.get('coach')
    category_id = request.GET.get('category')
    format = request.GET.get('format', 'html')

    # Calculate date range
    end_date = timezone.now()
    if period == '7d':
        start_date = end_date - timedelta(days=7)
    elif period == '30d':
        start_date = end_date - timedelta(days=30)
    elif period == '90d':
        start_date = end_date - timedelta(days=90)
    elif period == 'q':
        start_date = end_date - timedelta(days=90)  # Quarter
    elif period == 'y':
        start_date = end_date - timedelta(days=365)  # Year
    else:
        start_date = end_date - timedelta(days=30)

    # Get base orders
    orders = Order.objects.filter(
        club=club,
        status__in=['confirmed', 'completed'],
        created_at__range=[start_date, end_date]
    ).prefetch_related('items')

    # Apply filters
    if report_type == 'products':
        orders = orders.filter(items__product__isnull=False).distinct()
    elif report_type == 'services':
        orders = orders.filter(items__service__isnull=False).distinct()

    if coach_id:
        orders = orders.filter(
            Q(items__product__creator__userprofile__Coach_profile__id=coach_id) |
            Q(items__service__creator__userprofile__Coach_profile__id=coach_id)
        ).distinct()

    if category_id:
        orders = orders.filter(
            Q(items__product__creator__userprofile__Coach_profile__activity_type__id=category_id) |
            Q(items__service__creator__userprofile__Coach_profile__activity_type__id=category_id)
        ).distinct()

    # Prepare data for CSV export
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        filename = f"financial_report_{report_type}_{period}_{datetime.now().strftime('%Y%m%d')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        # Write header
        writer.writerow([
            'معرف الطلب', 'تاريخ', 'عميل', 'نوع العنصر', 'اسم العنصر',
            'التاجر', 'فئة', 'كمية', 'سعر', 'المجموع',
            'نسبة عمولة التاجر', 'ضريبة الهيئة', 'عمولة المنصة'
        ])

        # Write data rows
        for order in orders:
            for item in order.items.all():
                if report_type == 'products' and not item.product:
                    continue
                if report_type == 'services' and not item.service:
                    continue

                item_type = 'Product' if item.product else 'Service'
                item_name = item.product.title if item.product else item.service.title

                coach = None
                if item.product:
                    coach = item.product.creator.userprofile.Coach_profile if hasattr(item.product.creator,
                                                                                      'userprofile') else None
                elif item.service:
                    coach = item.service.creator.userprofile.Coach_profile if hasattr(item.service.creator,
                                                                                      'userprofile') else None

                category = coach.activity_type.name if coach and coach.activity_type else 'N/A'
                commission_rate = float(coach.get_current_commission_rate()) if coach else 0

                # Convert item price to float for consistent calculations
                price = float(item.price)
                quantity = item.quantity
                total_price = price * quantity

                # Calculate tax authority amount (15% VAT extraction)
                item_price_without_tax = round(price / 1.15, 2)
                tax_authority = round(price - item_price_without_tax, 2)

                # Calculate platform profit and fees
                taxable_amount = price - tax_authority
                platform_profit = round(taxable_amount * (commission_rate / 100), 2)
                platform_profit_tax = round(platform_profit * 0.15, 2)
                total_platform_fee = platform_profit + platform_profit_tax

                # Calculate commission and club revenue
                commission_amount = total_price * (commission_rate / 100) if coach else 0
                club_revenue = total_price - commission_amount

                # Assign calculated values to item for potential later use
                item.tax_authority = tax_authority
                item.item_price_without_tax = item_price_without_tax
                item.taxable_amount = taxable_amount
                item.platform_profit = platform_profit
                item.platform_profit_tax = platform_profit_tax
                item.total_platform_fee = total_platform_fee

                writer.writerow([
                    order.id,
                    order.created_at.strftime('%Y-%m-%d'),
                    f"{order.first_name} {order.last_name}",
                    item_type,
                    item_name,
                    coach.full_name if coach else 'N/A',
                    category,
                    quantity,
                    price,
                    total_price,
                    f"{commission_rate}%",
                    tax_authority,  # This is the tax amount (15% VAT)
                    platform_profit
                ])

        return response

    # For HTML view, prepare context
    coaches = CoachProfile.objects.filter(club=club)
    categories = Category.objects.filter(
        id__in=CoachProfile.objects.filter(club=club).values_list('activity_type', flat=True).distinct()
    )
    total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0

    context = {
        'club': club,
        'report_type': report_type,
        'period': period,
        'selected_coach': coach_id,
        'selected_category': category_id,
        'coaches': coaches,
        'total_revenue': total_revenue,
        'categories': categories,
        'orders': orders,
        'start_date': start_date,
        'end_date': end_date,
        'LANGUAGE_CODE': translation.get_language(),
    }

    return render(request, 'accountant_dashboard/custom_financial_reports.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Banner
from .forms import BannerForm


@login_required
def banner_management(request):
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    club = accountant_profile.club

    banners = Banner.objects.filter(club=club).order_by('-created_at')

    context = {
        'club': club,
        'banners': banners,
        'LANGUAGE_CODE': translation.get_language()
    }
    return render(request, 'accountant_dashboard/banner/banner_management.html', context)


from django.utils import translation
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import BannerForm  # Make sure the path is correct

@login_required
def add_banner(request):
    print("User is authenticated:", request.user.is_authenticated)

    if not hasattr(request.user.userprofile, 'accountant_profile'):
        print("User does not have an accountant profile. Redirecting...")
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    print("Accountant Profile:", accountant_profile)

    club = accountant_profile.club
    print("Club:", club)

    if request.method == 'POST':
        print("Request method is POST")
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)

        form = BannerForm(request.POST, request.FILES)
        print("Form created:", form)

        if form.is_valid():
            print("Form is valid")
            banner = form.save(commit=False)
            banner.club = club
            banner.save()
            print("Banner saved:", banner)
            messages.success(request, "Banner added successfully")
            return redirect('accountant_banner_management')
        else:
            print("Form is invalid:", form.errors)
    else:
        print("Request method is GET")
        form = BannerForm()
        print("Empty form created")

    context = {
        'club': club,
        'form': form,
        'LANGUAGE_CODE': translation.get_language()
    }
    print("Rendering template with context:", context)
    return render(request, 'accountant_dashboard/banner/add_banner.html', context)



@login_required
def edit_banner(request, banner_id):
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    club = accountant_profile.club

    banner = get_object_or_404(Banner, id=banner_id, club=club)

    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, "Banner updated successfully")
            return redirect('accountant_banner_management')
    else:
        form = BannerForm(instance=banner)

    context = {
        'club': club,
        'form': form,
        'banner': banner,
        'LANGUAGE_CODE': translation.get_language()
    }
    return render(request, 'accountant_dashboard/banner/edit_banner.html', context)


@login_required
def delete_banner(request, banner_id):
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    club = accountant_profile.club

    banner = get_object_or_404(Banner, id=banner_id, club=club)
    banner.delete()
    messages.success(request, "Banner deleted successfully")
    return redirect('accountant_banner_management')


# Add to accountant_dashboard/views.py
from django.http import HttpResponse
import csv
from datetime import datetime
from django.utils import timezone
from students.models import Order, OrderItem, ProductClick, ServiceClick
from accounts.models import CoachProfile


@login_required
def marketing_analysis_reports(request):
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    club = accountant_profile.club

    # Get filter parameters
    report_type = request.GET.get('report_type', 'clicks')
    period = request.GET.get('period', '30d')
    coach_id = request.GET.get('coach')
    category_id = request.GET.get('category')
    format = request.GET.get('format', 'html')

    # Calculate date range
    end_date = timezone.now()
    if period == '7d':
        start_date = end_date - timedelta(days=7)
    elif period == '30d':
        start_date = end_date - timedelta(days=30)
    elif period == '90d':
        start_date = end_date - timedelta(days=90)
    elif period == 'q':
        start_date = end_date - timedelta(days=90)  # Quarter
    elif period == 'y':
        start_date = end_date - timedelta(days=365)  # Year
    else:
        start_date = end_date - timedelta(days=30)

    # Prepare data for CSV export
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        filename = f"marketing_report_{report_type}_{period}_{datetime.now().strftime('%Y%m%d')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        if report_type == 'clicks':
            # Write header for clicks report
            writer.writerow([
                 'نوع العنصر', 'اسم العنصر', 'التاجر', 'الفئة',
                'عدد النقرات', 'المستخدمون الفريدون', 'معدل التحويل'
            ])

            # Build filtered queries for product clicks
            product_clicks_query = ProductClick.objects.filter(
                product__club=club,
                timestamp__range=[start_date, end_date]
            )

            if coach_id:
                product_clicks_query = product_clicks_query.filter(
                    product__creator__userprofile__Coach_profile__id=coach_id
                )

            if category_id:
                product_clicks_query = product_clicks_query.filter(
                    product__creator__userprofile__Coach_profile__activity_type__id=category_id
                )

            # Build filtered queries for service clicks
            service_clicks_query = ServiceClick.objects.filter(
                service__club=club,
                timestamp__range=[start_date, end_date]
            )

            if coach_id:
                service_clicks_query = service_clicks_query.filter(
                    service__creator__userprofile__Coach_profile__id=coach_id
                )

            if category_id:
                service_clicks_query = service_clicks_query.filter(
                    service__creator__userprofile__Coach_profile__activity_type__id=category_id
                )

            # Get aggregated product clicks data using the filtered query
            product_clicks = product_clicks_query.values(
                'product__title',
                'product__creator__userprofile__Coach_profile__full_name',
                'product__creator__userprofile__Coach_profile__activity_type__name'
            ).annotate(
                click_count=Count('id'),
                unique_users=Count('user', distinct=True)
            ).order_by('-click_count')

            # Get aggregated service clicks data using the filtered query
            service_clicks = service_clicks_query.values(
                'service__title',
                'service__creator__userprofile__Coach_profile__full_name',
                'service__creator__userprofile__Coach_profile__activity_type__name'
            ).annotate(
                click_count=Count('id'),
                unique_users=Count('user', distinct=True)
            ).order_by('-click_count')

            # Write product clicks data
            for click in product_clicks:
                # Build orders query with same filters
                orders_query = Order.objects.filter(
                    items__product__title=click['product__title'],
                    created_at__range=[start_date, end_date],
                    club=club,
                    status__in=['confirmed', 'completed']
                )

                if coach_id:
                    orders_query = orders_query.filter(
                        items__product__creator__userprofile__Coach_profile__id=coach_id
                    )

                if category_id:
                    orders_query = orders_query.filter(
                        items__product__creator__userprofile__Coach_profile__activity_type__id=category_id
                    )

                orders_count = orders_query.count()
                conversion_rate = (orders_count / click['click_count']) * 100 if click['click_count'] > 0 else 0

                writer.writerow([
                    'منتج',  # Product in Arabic
                    click['product__title'],
                    click['product__creator__userprofile__Coach_profile__full_name'],
                    click['product__creator__userprofile__Coach_profile__activity_type__name'],
                    click['click_count'],
                    click['unique_users'],
                    f"{conversion_rate:.2f}%"
                ])

            # Write service clicks data
            for click in service_clicks:
                # Build orders query with same filters
                orders_query = Order.objects.filter(
                    items__service__title=click['service__title'],
                    created_at__range=[start_date, end_date],
                    club=club,
                    status__in=['confirmed', 'completed']
                )

                if coach_id:
                    orders_query = orders_query.filter(
                        items__service__creator__userprofile__Coach_profile__id=coach_id
                    )

                if category_id:
                    orders_query = orders_query.filter(
                        items__service__creator__userprofile__Coach_profile__activity_type__id=category_id
                    )

                orders_count = orders_query.count()
                conversion_rate = (orders_count / click['click_count']) * 100 if click['click_count'] > 0 else 0

                writer.writerow([
                    'خدمة',  # Service in Arabic
                    click['service__title'],
                    click['service__creator__userprofile__Coach_profile__full_name'],
                    click['service__creator__userprofile__Coach_profile__activity_type__name'],
                    click['click_count'],
                    click['unique_users'],
                    f"{conversion_rate:.2f}%"
                ])

        elif report_type == 'conversions':
            # Write header for conversions report
            writer.writerow([
             'نوع العنصر', 'اسم العنصر', 'التاجر', 'الفئة',
                'المشاهدات', 'الطلبات', 'معدل التحويل', 'الإيرادات'
            ])

            # Build filtered query for products with orders
            products_query = OrderItem.objects.filter(
                order__club=club,
                order__created_at__range=[start_date, end_date],
                order__status__in=['confirmed', 'completed'],
                product__isnull=False
            )

            if coach_id:
                products_query = products_query.filter(
                    product__creator__userprofile__Coach_profile__id=coach_id
                )

            if category_id:
                products_query = products_query.filter(
                    product__creator__userprofile__Coach_profile__activity_type__id=category_id
                )

            products = products_query.values(
                'product__title',
                'product__creator__userprofile__Coach_profile__full_name',
                'product__creator__userprofile__Coach_profile__activity_type__name'
            ).annotate(
                order_count=Count('id'),
                revenue=Sum(F('price') * F('quantity'))
            ).order_by('-revenue')

            # Build filtered query for services with orders
            services_query = OrderItem.objects.filter(
                order__club=club,
                order__created_at__range=[start_date, end_date],
                order__status__in=['confirmed', 'completed'],
                service__isnull=False
            )

            if coach_id:
                services_query = services_query.filter(
                    service__creator__userprofile__Coach_profile__id=coach_id
                )

            if category_id:
                services_query = services_query.filter(
                    service__creator__userprofile__Coach_profile__activity_type__id=category_id
                )

            services = services_query.values(
                'service__title',
                'service__creator__userprofile__Coach_profile__full_name',
                'service__creator__userprofile__Coach_profile__activity_type__name'
            ).annotate(
                order_count=Count('id'),
                revenue=Sum(F('price') * F('quantity'))
            ).order_by('-revenue')

            # Write product data
            for product in products:
                # Get view count with same filters
                view_query = ProductClick.objects.filter(
                    product__title=product['product__title'],
                    timestamp__range=[start_date, end_date],
                    product__club=club
                )

                if coach_id:
                    view_query = view_query.filter(
                        product__creator__userprofile__Coach_profile__id=coach_id
                    )

                if category_id:
                    view_query = view_query.filter(
                        product__creator__userprofile__Coach_profile__activity_type__id=category_id
                    )

                view_count = view_query.count()
                conversion_rate = (product['order_count'] / view_count) * 100 if view_count > 0 else 0

                writer.writerow([
                    'منتج',
                    product['product__title'],
                    product['product__creator__userprofile__Coach_profile__full_name'],
                    product['product__creator__userprofile__Coach_profile__activity_type__name'],
                    view_count,
                    product['order_count'],
                    f"{conversion_rate:.2f}%",
                    product['revenue']
                ])

            # Write service data
            for service in services:
                # Get view count with same filters
                view_query = ServiceClick.objects.filter(
                    service__title=service['service__title'],
                    timestamp__range=[start_date, end_date],
                    service__club=club
                )

                if coach_id:
                    view_query = view_query.filter(
                        service__creator__userprofile__Coach_profile__id=coach_id
                    )

                if category_id:
                    view_query = view_query.filter(
                        service__creator__userprofile__Coach_profile__activity_type__id=category_id
                    )

                view_count = view_query.count()
                conversion_rate = (service['order_count'] / view_count) * 100 if view_count > 0 else 0

                writer.writerow([
                    'خدمة',
                    service['service__title'],
                    service['service__creator__userprofile__Coach_profile__full_name'],
                    service['service__creator__userprofile__Coach_profile__activity_type__name'],
                    view_count,
                    service['order_count'],
                    f"{conversion_rate:.2f}%",
                    service['revenue']
                ])

        return response

    # For HTML view, prepare context with proper filtering
    coaches = CoachProfile.objects.filter(club=club)
    categories = Category.objects.filter(
        id__in=CoachProfile.objects.filter(club=club).values_list('activity_type', flat=True).distinct()
    )

    # Calculate summary statistics with filters applied
    if report_type == 'clicks':
        # Build filtered queries for summary
        product_clicks_summary = ProductClick.objects.filter(
            product__club=club,
            timestamp__range=[start_date, end_date]
        )
        service_clicks_summary = ServiceClick.objects.filter(
            service__club=club,
            timestamp__range=[start_date, end_date]
        )

        if coach_id:
            product_clicks_summary = product_clicks_summary.filter(
                product__creator__userprofile__Coach_profile__id=coach_id
            )
            service_clicks_summary = service_clicks_summary.filter(
                service__creator__userprofile__Coach_profile__id=coach_id
            )

        if category_id:
            product_clicks_summary = product_clicks_summary.filter(
                product__creator__userprofile__Coach_profile__activity_type__id=category_id
            )
            service_clicks_summary = service_clicks_summary.filter(
                service__creator__userprofile__Coach_profile__activity_type__id=category_id
            )

        total_clicks = product_clicks_summary.count() + service_clicks_summary.count()

        # Build filtered orders query for summary
        orders_query_summary = Order.objects.filter(
            club=club,
            created_at__range=[start_date, end_date],
            status__in=['confirmed', 'completed']
        )

        if coach_id:
            orders_query_summary = orders_query_summary.filter(
                Q(items__product__creator__userprofile__Coach_profile__id=coach_id) |
                Q(items__service__creator__userprofile__Coach_profile__id=coach_id)
            ).distinct()

        if category_id:
            orders_query_summary = orders_query_summary.filter(
                Q(items__product__creator__userprofile__Coach_profile__activity_type__id=category_id) |
                Q(items__service__creator__userprofile__Coach_profile__activity_type__id=category_id)
            ).distinct()

        total_orders = orders_query_summary.count()
        conversion_rate = (total_orders / total_clicks * 100) if total_clicks > 0 else 0
    else:
        total_clicks = None
        total_orders = None
        conversion_rate = None

    context = {
        'club': club,
        'report_type': report_type,
        'period': period,
        'coach_id': coach_id,  # Make sure to pass the actual coach_id
        'category_id': category_id,  # Make sure to pass the actual category_id
        'coaches': coaches,
        'categories': categories,
        'start_date': start_date,
        'end_date': end_date,
        'total_clicks': total_clicks,
        'total_orders': total_orders,
        'conversion_rate': round(conversion_rate, 2) if conversion_rate is not None else None,
        'LANGUAGE_CODE': translation.get_language(),
    }

    return render(request, 'accountant_dashboard/marketing/marketing_analysis_reports.html', context)


@login_required
def expense_analytics(request):
    # Verify user is an accountant
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    club = accountant_profile.club

    # Date range for reports (last 30 days by default)
    time_period = request.GET.get('period', '30d')
    end_date = timezone.now()

    if time_period == '7d':
        start_date = end_date - timedelta(days=7)
    elif time_period == '30d':
        start_date = end_date - timedelta(days=30)
    elif time_period == '90d':
        start_date = end_date - timedelta(days=90)
    elif time_period == '12m':
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)
        time_period = '30d'

    # Get all cancelled orders (expenses)
    expenses = Order.objects.filter(
        club=club,
        status='cancelled',
        created_at__range=[start_date, end_date]
    )

    # Expense by day
    expense_by_day = (
        expenses.annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total=Sum('total_price'))
        .order_by('day')
    )

    # Expense by category
    expense_by_category = (
        expenses.annotate(
            category_name=Case(
                When(items__product__isnull=False,
                     then=F('items__product__creator__userprofile__Coach_profile__activity_type__name')),
                When(items__service__isnull=False,
                     then=F('items__service__creator__userprofile__Coach_profile__activity_type__name')),
                output_field=models.CharField()
            )
        )
        .values('category_name')
        .annotate(total=Sum('total_price'))
        .filter(category_name__isnull=False)
        .order_by('-total')
    )

    # Expense by coach
    expense_by_coach = (
        expenses.annotate(
            coach_name=Case(
                When(items__product__isnull=False,
                     then=F('items__product__creator__userprofile__Coach_profile__full_name')),
                When(items__service__isnull=False,
                     then=F('items__service__creator__userprofile__Coach_profile__full_name')),
                output_field=models.CharField()
            )
        )
        .values('coach_name')
        .annotate(total=Sum('total_price'))
        .filter(coach_name__isnull=False)
        .order_by('-total')
    )

    # Prepare chart data
    expense_dates = [entry['day'].strftime('%Y-%m-%d') for entry in expense_by_day]
    expense_amounts = [float(entry['total']) for entry in expense_by_day]

    category_labels = [entry['category_name'] for entry in expense_by_category[:5]]
    category_data = [float(entry['total']) for entry in expense_by_category[:5]]

    coach_labels = [entry['coach_name'] for entry in expense_by_coach[:5]]
    coach_data = [float(entry['total']) for entry in expense_by_coach[:5]]

    total_expenses = expenses.aggregate(total=Sum('total_price'))['total'] or 0

    context = {
        'club': club,
        'time_period': time_period,
        'total_expenses': total_expenses,
        'expense_dates': json.dumps(expense_dates),
        'expense_amounts': json.dumps(expense_amounts),
        'expense_by_category': expense_by_category,
        'expense_by_coach': expense_by_coach,
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'coach_labels': json.dumps(coach_labels),
        'coach_data': json.dumps(coach_data),
        'LANGUAGE_CODE': translation.get_language(),
    }

    return render(request, 'accountant_dashboard/expenses/expense_analytics.html', context)




from .models import LandingPageContent, TermsAndConditions
from .forms import LandingPageContentForm, TermsAndConditionsForm


@login_required
def cms_settings(request):
    if not hasattr(request.user.userprofile, 'accountant_profile'):
        return redirect('club_dashboard_index')

    accountant_profile = request.user.userprofile.accountant_profile
    club = accountant_profile.club
    landing_content, created = LandingPageContent.objects.get_or_create(club=club)
    terms_content, created = TermsAndConditions.objects.get_or_create(club=club)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'landing':
            # Handle landing page form
            landing_form = LandingPageContentForm(request.POST, instance=landing_content)
            if landing_form.is_valid():
                landing_instance = landing_form.save(commit=False)
                landing_instance.club = club
                landing_instance.save()
                messages.success(request, "Landing page content updated successfully")
                return redirect('accountant_cms_settings')
            else:
                # Keep the current terms form for display
                terms_form = TermsAndConditionsForm(instance=terms_content)

        elif form_type == 'terms':
            # Handle terms form
            terms_form = TermsAndConditionsForm(request.POST, instance=terms_content)
            if terms_form.is_valid():
                terms_instance = terms_form.save(commit=False)
                terms_instance.club = club
                terms_instance.save()
                messages.success(request, "Terms & Conditions updated successfully")
                return redirect('accountant_cms_settings')
            else:
                # Keep the current landing form for display
                landing_form = LandingPageContentForm(instance=landing_content)
    else:
        landing_form = LandingPageContentForm(instance=landing_content)
        terms_form = TermsAndConditionsForm(instance=terms_content)

    context = {
        'club': club,
        'landing_form': landing_form,
        'terms_form': terms_form,
        'LANGUAGE_CODE': translation.get_language(),
    }
    return render(request, 'accountant_dashboard/cms_settings.html', context)



