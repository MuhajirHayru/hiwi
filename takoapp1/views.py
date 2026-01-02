import json
import uuid
from django.utils.timezone import now, timedelta
from django.contrib.auth.hashers import make_password

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Product, Cart, CartItem, Order, User
from .serializers import ProductSerializer, OrderSerializer

# ======================
# PRODUCT VIEWS
# ======================

class ProductCreateAPIView(generics.CreateAPIView):
    """Admin role to create products with an image."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    parser_classes = [MultiPartParser, FormParser]

class ProductListAPIView(generics.ListAPIView):
    """Public list of active products."""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer

class Confirm(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, Update or Delete a specific product."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = "pk"

# ======================
# ORDER & CART LOGIC
# ======================

class OrderCreateAPIView(APIView):
    """
    Handles the Checkout process from React.
    1. Creates a Cart (satisfying session_id requirements).
    2. Parses cart items from JSON string.
    3. Creates Order with Payment Screenshot.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        data = request.data
        try:
            # 1. Create the Cart
            # Since your model has default=uuid.uuid4, we don't pass session_id.
            # Django will generate a unique one automatically.
            cart = Cart.objects.create()

            # 2. Parse items (Sent as JSON string via FormData)
            items_json = data.get("items", "[]")
            items_list = json.loads(items_json)

            if not items_list:
                return Response({"error": "Your shopping bag is empty"}, status=status.HTTP_400_BAD_REQUEST)

            # 3. Create the Order object first
            # customer_name maps to 'username' sent from React form
            order = Order.objects.create(
                customer_name=data.get("username"),
                cart=cart,
                payment_screenshot=request.FILES.get("payment_screenshot"),
                status="PENDING"
            )

            # 4. Save each item into CartItem and link to the Order
            for item_data in items_list:
                try:
                    product = Product.objects.get(id=item_data['id'])
                    
                    cart_item = CartItem.objects.create(
                        cart=cart,
                        product=product,
                        quantity=item_data.get('quantity', 1),
                        size=item_data.get('size', 'M'),
                        color=item_data.get('color', 'Default')
                    )
                    
                    # Link this specific cart item to the Order's ManyToMany field
                    order.items.add(cart_item)
                except Product.DoesNotExist:
                    continue # Or handle as error if a product ID is invalid

            return Response({
                "order_id": order.id,
                "message": "Order placed successfully! Pending verification."
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Checkout Error: {str(e)}")
            return Response({"error": "Failed to process order. Ensure all fields are valid."}, status=status.HTTP_400_BAD_REQUEST)

# ======================
# ADMIN / ANALYTICS UTILITIES
# ======================

class ConfirmOrderAPIView(APIView):
    """Updates Order status to CONFIRMED."""
    def patch(self, request, pk):
        try:
            order = Order.objects.get(id=pk)
            order.status = "CONFIRMED"
            order.save()
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

class WeeklyOrdersAPIView(APIView):
    """Analytics for total orders in the last 7 days."""
    def get(self, request):
        week_ago = now().date() - timedelta(days=7)
        total = Order.objects.filter(created_at__date__gte=week_ago).count()
        return Response({"weekly_orders": total})

class CreateSalesUserAPIView(APIView):
    """Create a user with Sales Admin permissions."""
    def post(self, request):
        try:
            user = User.objects.create(
                username=request.data["username"],
                password=make_password(request.data["password"]),
                is_sales_admin=True
            )
            return Response({"username": user.username, "status": "Sales admin created"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class OrderListAPIView(generics.ListAPIView):
    """View to look at all ordered items (useful for Admin panel)."""
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer