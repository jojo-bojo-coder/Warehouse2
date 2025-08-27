from rest_framework import serializers
from .models import (
    ProductsModel, ProductsClassificationModel, ProductsImage, ProductsRate,
    ServicesModel, ServicesClassificationModel, ServicesImage, ServicesRate,
    Blog, BlogClassificationModel, ServiceOrderModel, CartItem, ServiceCartItem,
    Order, OrderItem, OrderCancellation, Review, ProductClick, ServiceClick
)
from accounts.models import UserProfile, StudentProfile, CoachProfile, ClubsModel
from accounts.serializers import UserProfileSerializer, StudentProfileSerializer, CoachProfileSerializer, ClubsModelSerializer
from club_dashboard.models import DashboardSettings, RefundDispute, RefundDisputeMessage, RefundDisputeAttachment
from coach_dashboard.models import Coupon, CouponActivation


class ProductsClassificationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductsClassificationModel
        fields = '__all__'


class ProductsImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductsImage
        fields = '__all__'


class ProductsRateSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(source='user.userprofile', read_only=True)

    class Meta:
        model = ProductsRate
        fields = '__all__'


class ProductsModelSerializer(serializers.ModelSerializer):
    classification = ProductsClassificationModelSerializer(many=True, read_only=True)
    images = ProductsImageSerializer(many=True, read_only=True)
    reviews = ProductsRateSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    can_be_sold = serializers.BooleanField(read_only=True)
    tax_authority_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    platform_profit_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    platform_profit_tax = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_platform_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    vendor_net_profit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ProductsModel
        fields = '__all__'


class ServicesClassificationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicesClassificationModel
        fields = '__all__'


class ServicesImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicesImage
        fields = '__all__'


class ServicesRateSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(source='user.userprofile', read_only=True)

    class Meta:
        model = ServicesRate
        fields = '__all__'


class ServicesModelSerializer(serializers.ModelSerializer):
    classification = ServicesClassificationModelSerializer(many=True, read_only=True)
    images = ServicesImageSerializer(many=True, read_only=True)
    reviews = ServicesRateSerializer(many=True, read_only=True)
    coaches = CoachProfileSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    monthly_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_subscription_days = serializers.IntegerField(read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    can_be_sold = serializers.BooleanField(read_only=True)
    tax_authority_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    platform_profit_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    platform_profit_tax = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_platform_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    vendor_net_profit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ServicesModel
        fields = '__all__'


class BlogClassificationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogClassificationModel
        fields = '__all__'


class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = '__all__'


class ServiceOrderModelSerializer(serializers.ModelSerializer):
    service = ServicesModelSerializer(read_only=True)

    class Meta:
        model = ServiceOrderModel
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductsModelSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = '__all__'


class ServiceCartItemSerializer(serializers.ModelSerializer):
    service = ServicesModelSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ServiceCartItem
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductsModelSerializer(read_only=True)
    service = ServicesModelSerializer(read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    vendor_commission_info = serializers.DictField(read_only=True)
    order_type = serializers.CharField(read_only=True)
    order_type_display = serializers.CharField(read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    order_type = serializers.CharField(read_only=True)
    order_type_display = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = '__all__'


class OrderCancellationSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    reason_display_text = serializers.CharField(read_only=True)

    class Meta:
        model = OrderCancellation
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    student = StudentProfileSerializer(read_only=True)
    order = OrderSerializer(read_only=True)
    order_item = OrderItemSerializer(read_only=True)
    product = ProductsModelSerializer(read_only=True)
    service = ServicesModelSerializer(read_only=True)
    reviewed_item = serializers.SerializerMethodField()
    reviewed_item_type = serializers.CharField(read_only=True)
    order_status = serializers.CharField(read_only=True)
    is_visible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Review
        fields = '__all__'

    def get_reviewed_item(self, obj):
        if obj.product:
            return ProductsModelSerializer(obj.product).data
        elif obj.service:
            return ServicesModelSerializer(obj.service).data
        return None


class ProductClickSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    product = ProductsModelSerializer(read_only=True)

    class Meta:
        model = ProductClick
        fields = '__all__'


class ServiceClickSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    service = ServicesModelSerializer(read_only=True)

    class Meta:
        model = ServiceClick
        fields = '__all__'


class DashboardSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardSettings
        fields = '__all__'


class RefundDisputeAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundDisputeAttachment
        fields = '__all__'


class RefundDisputeMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundDisputeMessage
        fields = '__all__'


class RefundDisputeSerializer(serializers.ModelSerializer):
    attachments = RefundDisputeAttachmentSerializer(many=True, read_only=True)
    messages = RefundDisputeMessageSerializer(many=True, read_only=True)

    class Meta:
        model = RefundDispute
        fields = '__all__'


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'


class CouponActivationSerializer(serializers.ModelSerializer):
    coupon = CouponSerializer(read_only=True)

    class Meta:
        model = CouponActivation
        fields = '__all__'


class StudentDashboardSerializer(serializers.Serializer):
    """Serializer for student dashboard data"""
    coaches = CoachProfileSerializer(many=True)
    students = StudentProfileSerializer(many=True)
    club = ClubsModelSerializer()
    services = ServicesModelSerializer(many=True)
    products = ProductsModelSerializer(many=True)
    service_orders = ServiceOrderModelSerializer(many=True)
    today = serializers.DateTimeField()
    three_days_from_now = serializers.DateTimeField()
    show_employee_client_counts = serializers.BooleanField()


class CartSummarySerializer(serializers.Serializer):
    """Serializer for cart summary data"""
    product_items = CartItemSerializer(many=True)
    service_items = ServiceCartItemSerializer(many=True)
    product_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    service_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    original_service_total = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    total_service_savings = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    original_total_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    total_savings = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    has_service_discounts = serializers.BooleanField()


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout data"""
    product_items = CartItemSerializer(many=True)
    service_items = ServiceCartItemSerializer(many=True)
    product_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    service_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_after_discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    applied_coupon = serializers.DictField(required=False)
    user = UserProfileSerializer()
    student = StudentProfileSerializer()


class ProductsViewSerializer(serializers.Serializer):
    """Serializer for products view data"""
    products = ProductsModelSerializer(many=True)
    total_products = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    club = ClubsModelSerializer()


class ServicesViewSerializer(serializers.Serializer):
    """Serializer for services view data"""
    services = ServicesModelSerializer(many=True)
    classifications = serializers.ListField()
    avg_monthly_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_duration_hours = serializers.IntegerField()
    avg_duration_minutes = serializers.IntegerField()
    pricing_periods = serializers.ListField()
    PRICING_PERIOD_CHOICES = serializers.ListField()


class ArticlesViewSerializer(serializers.Serializer):
    """Serializer for articles view data"""
    arts = BlogSerializer(many=True)
    featured_article = BlogSerializer(required=False)
    club = ClubsModelSerializer()